"""抓取公开地图数据。

高程: Mapzen/AWS Terrain Tiles (terrarium 编码；本区域主要来自 SRTM，公有领域)
      https://registry.opendata.aws/terrain-tiles
矢量: Natural Earth 10m（公有领域）https://www.naturalearthdata.com

用法: python fetch_map.py <work_dir>
产出: <work_dir>/map/elev_z8.npy  华南细部 (z8, 瓦片 x199-217, y102-114)
      <work_dir>/map/elev_z7.npy  东南亚高地全景 (z7, 瓦片 x94-109, y49-61)
"""
import io
import os
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import requests
from PIL import Image

OUT = sys.argv[1] + '/map'
PRESETS = {
    'z8': (8, 199, 217, 102, 114),
    'z7': (7, 94, 109, 49, 61),
}


def tile(args):
    z, x, y = args
    p = f'{OUT}/tiles/{z}_{x}_{y}.png'
    if os.path.exists(p) and os.path.getsize(p) > 0:
        return p
    url = f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'
    for _ in range(5):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                open(p, 'wb').write(r.content)
                return p
        except Exception:
            pass
    raise RuntimeError(f'failed {url}')


def main():
    os.makedirs(OUT + '/tiles', exist_ok=True)
    for name, (z, x0, x1, y0, y1) in PRESETS.items():
        xs, ys = range(x0, x1 + 1), range(y0, y1 + 1)
        with ThreadPoolExecutor(12) as ex:
            list(ex.map(tile, [(z, x, y) for x in xs for y in ys]))
        elev = np.zeros((256 * len(ys), 256 * len(xs)), np.float32)
        for i, y in enumerate(ys):
            for j, x in enumerate(xs):
                a = np.asarray(Image.open(f'{OUT}/tiles/{z}_{x}_{y}.png').convert('RGB'), dtype=np.float32)
                elev[i * 256:(i + 1) * 256, j * 256:(j + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
        np.save(f'{OUT}/elev_{name}.npy', elev)
        print(name, elev.shape, float(elev.min()), float(elev.max()))
    for name in ['ne_10m_coastline', 'ne_10m_rivers_lake_centerlines', 'ne_10m_lakes']:
        d = f'{OUT}/{name}'
        if os.path.exists(f'{d}/{name}.shp'):
            continue
        r = requests.get(f'https://naciscdn.org/naturalearth/10m/physical/{name}.zip', timeout=120)
        r.raise_for_status()
        zipfile.ZipFile(io.BytesIO(r.content)).extractall(d)
        print('got', name, len(r.content))


if __name__ == '__main__':
    main()
