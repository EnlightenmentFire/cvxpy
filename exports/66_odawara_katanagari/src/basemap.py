import numpy as np, math, json, glob, sys
from PIL import Image
from scipy import ndimage as ndi
from shapely.geometry import shape, box, Polygon, MultiPolygon
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
from geo import merc
D = "/tmp/claude-0/work/dem/"; A = "/tmp/claude-0/work/od/assets/"; G = "/tmp/claude-0/work/geo/"

def mosaic(z):
    fs = glob.glob(f"{D}{z}_*_*.png")
    xs = sorted({int(f.split('/')[-1].split('_')[1]) for f in fs}); ys = sorted({int(f.split('_')[-1][:-4]) for f in fs})
    H = np.zeros(((ys[-1]-ys[0]+1)*256, (xs[-1]-xs[0]+1)*256), np.float32)
    for f in fs:
        _, x, y = f.split('/')[-1][:-4].split('_'); x = int(x); y = int(y)
        a = np.asarray(Image.open(f).convert('RGB')).astype(np.float32)
        H[(y-ys[0])*256:(y-ys[0]+1)*256, (x-xs[0])*256:(x-xs[0]+1)*256] = a[...,0]*256 + a[...,1] + a[...,2]/256 - 32768
    return H, xs[0], ys[0]

def ramp(h):
    st = [(-3000,(14,24,32)),(0,(78,80,58)),(60,(82,88,62)),(250,(74,84,58)),(700,(80,86,62)),(1400,(96,96,76)),
          (2200,(116,112,96)),(3000,(150,146,138)),(4000,(176,174,170))]
    xs = [s[0] for s in st]; out = np.zeros(h.shape+(3,), np.float32)
    for c in range(3): out[...,c] = np.interp(h, xs, [s[1][c] for s in st])
    return out

def raster_poly(geoms, z, ox, oy, shape_):
    from PIL import ImageDraw
    im = Image.new('L', (shape_[1], shape_[0]), 0); dr = ImageDraw.Draw(im)
    def ring(r): return [(merc(x, y, z)[0]-ox, merc(x, y, z)[1]-oy) for x, y in r.coords]
    for g in geoms:
        ps = [g] if isinstance(g, Polygon) else list(g.geoms)
        for p in ps:
            dr.polygon(ring(p.exterior), fill=255)
            for i in p.interiors: dr.polygon(ring(i), fill=0)
    return np.asarray(im) > 127

def build(name, z, lonlat_box, exag, aral=False, dem_water=False):
    H, tx, ty = mosaic(z)
    ox, oy = tx*256, ty*256
    l0, l1, b0, b1 = lonlat_box
    x0, y1 = merc(l0, b0, z); x1, y0 = merc(l1, b1, z)
    cx0, cy0, cx1, cy1 = int(x0-ox), int(y0-oy), int(x1-ox), int(y1-oy)
    H = H[cy0:cy1, cx0:cx1]; ox += cx0; oy += cy0
    bb = box(l0-2, b0-2, l1+2, b1+2)
    if dem_water:
        low = H < 0.5
        lab, _ = ndi.label(low)
        ids = set(np.unique(lab[-1, :])) | set(np.unique(lab[:, -1])) - {0}
        water = np.isin(lab, [i for i in ids if i])
        water = ndi.binary_closing(water, iterations=6) | (ndi.gaussian_filter(H, 3) < -3)
        water = ndi.binary_opening(water, iterations=3)
        water = ndi.gaussian_filter(water.astype(np.float32), 4) > 0.5
        lab2, n2 = ndi.label(~water)
        if n2 > 1:
            sz = ndi.sum(np.ones_like(water), lab2, range(1, n2 + 1)); big = 1 + int(np.argmax(sz))
            water = lab2 != big
    else:
        land = json.load(open(G + "ne_10m_land.geojson"))
        lg = [shape(f['geometry']).intersection(bb) for f in land['features'] if shape(f['geometry']).intersects(bb)]
        landm = raster_poly([g for g in lg if not g.is_empty], z, ox, oy, H.shape)
        water = ~landm
    lakes = json.load(open(G + "ne_10m_lakes.geojson"))
    keep = {"Biwa-ko", "Lake Biwa", "Kasumiga-ura", "Ashino-ko", "Inawashiro-ko"}
    lk = [shape(f['geometry']) for f in lakes['features'] if (f['properties'].get('name') in keep) and shape(f['geometry']).intersects(bb)]
    if lk: water |= raster_poly(lk, z, ox, oy, H.shape)
    if aral:  # historical (pre-1960) Aral Sea, shown schematically: DEM basin below 53 m connected to its centre
        sx, sy = merc(59.6, 45.0, z); sx -= ox; sy -= oy
        if 0 <= sx < H.shape[1] and 0 <= sy < H.shape[0]:
            low = ndi.gaussian_filter(H, 1.0) < 53
            lab, _ = ndi.label(low); k = lab[int(sy), int(sx)]
            if k: water |= ndi.binary_opening(lab == k, iterations=2)
    Hs = ndi.gaussian_filter(np.where(water, np.minimum(H, -50), H), 0.9)
    mpp = 156543.03 * math.cos(math.radians((b0+b1)/2)) / 2**z
    gy, gx = np.gradient(Hs*exag/mpp)
    def hs(az, alt=40):
        az = math.radians(az); alt = math.radians(alt)
        lx = math.sin(az)*math.cos(alt); ly = math.cos(az)*math.cos(alt); lz = math.sin(alt)
        return np.clip((-gx*lx + gy*ly + lz)/np.sqrt(gx*gx+gy*gy+1), 0, 1)
    s = 0.65*hs(315) + 0.2*hs(260) + 0.15*hs(20)
    rel = s - math.sin(math.radians(40))
    rgb = ramp(Hs) * (1 + 1.15*rel[..., None])
    loc = Hs - ndi.gaussian_filter(Hs, 14)
    rgb *= (1 + np.clip(loc/1200, -0.2, 0.22))[..., None]
    wd = ndi.distance_transform_edt(water)
    sea = np.array([16, 30, 40], np.float32)
    deep = np.clip(wd/40, 0, 1)[..., None]
    wcol = sea*(1.25-0.35*deep)
    rgb = np.where(water[..., None], wcol, rgb)
    # shoreline glow
    ld = ndi.distance_transform_edt(~water)
    edge = np.exp(-ld/2.0)*(~water)
    rgb += edge[..., None]*np.array([30, 40, 44])
    # grade: darker, cooler shadows
    lum = rgb.mean(-1, keepdims=True)
    rgb = rgb*0.78 + (lum*0.78 - rgb*0.78)*0.18
    rgb[..., 2] += (1-s[...,None][...,0])*6
    rng = np.random.default_rng(3)
    rgb += (ndi.gaussian_filter(rng.normal(0, 1, H.shape), 1.3)*4 + rng.normal(0, 1, H.shape)*1.5)[..., None]
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    Image.fromarray(rgb).save(f"{A}base_{name}.png")
    np.save(f"{A}water_{name}.npy", water)
    json.dump(dict(z=z, x0=ox/256, y0=oy/256, w=H.shape[1], h=H.shape[0], box=lonlat_box), open(f"{A}base_{name}.json", "w"))
    print(name, H.shape)

if __name__ == "__main__":
    which = sys.argv[1:] or ["japan", "kanto", "odawara"]
    if "japan" in which: build("japan", 8, (128.5, 143.0, 30.0, 39.6), 4.0)
    if "kanto" in which: build("kanto", 10, (138.0, 140.9, 34.4, 36.9), 2.6)
    if "odawara" in which: build("odawara", 14, (139.03, 139.27, 35.16, 35.34), 1.4, dem_water=True)
