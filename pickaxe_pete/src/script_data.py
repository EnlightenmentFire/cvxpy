# Fixed script. Each line: (id, scene, speaker, subtitle_text, tts_text, gap_before_seconds, style)
# tts_text may differ only in punctuation/emphasis hints for the voice engine; meaning is identical.
# style: tags used by voice gen (shout / deadpan / boom) and by the mixer.

LINES = [
    # SCENE 1
    ("s1_pete", 1, "PETE", "Forty years of digging and all I've found is sand and a very disappointed mule.",
     "Forty years of digging... and all I've found is sand, and a very disappointed mule!", 2.6, "normal"),
    # SCENE 2
    ("s2_pete1", 2, "PETE", "Gold mine! Stand back, I'll start digging!",
     "Gold mine! Stand back, I'll start digging!", 0.9, "shout"),
    ("s2_zoe1", 2, "ZOE", "Please don't hit Riggy.",
     "Please don't hit Riggy.", 0.25, "deadpan"),
    ("s2_riggy1", 2, "RIGGY", "WELCOME, CHALLENGER! TO THE MINE!",
     "Welcome, challenger! To the mine!", 0.25, "boom"),
    ("s2_pete2", 2, "PETE", "...Where's the dirt?",
     "Where's the dirt?", 0.9, "normal"),
    ("s2_zoe2", 2, "ZOE", "There is no dirt. We mine by guessing.",
     "There is no dirt. We mine by guessing.", 0.3, "deadpan"),
    # SCENE 3
    ("s3_zoe1", 3, "ZOE", "Imagine one giant notebook of who paid who. Everybody keeps the same copy, so nobody can cheat.",
     "Imagine one giant notebook of who paid who. Everybody keeps the same copy, so nobody can cheat.", 1.2, "deadpan"),
    ("s3_pete1", 3, "PETE", "Sounds like the saloon tab. Except honest.",
     "Sounds like the saloon tab. Except honest.", 0.3, "normal"),
    ("s3_zoe2", 3, "ZOE", "Every few minutes, somebody gets to write the next page.",
     "Every few minutes, somebody gets to write the next page.", 0.3, "deadpan"),
    # SCENE 4
    ("s4_zoe1", 4, "ZOE", "To win the pen, you have to guess a magic number. No skill. No trick. Just guessing.",
     "To win the pen, you have to guess a magic number. No skill. No trick. Just guessing.", 1.0, "deadpan"),
    ("s4_riggy1", 4, "RIGGY", "I GUESS ONE HUNDRED TRILLION TIMES A SECOND! I AM VERY GOOD AT BEING WRONG!",
     "I guess one hundred trillion times a second! I am very good at being wrong!", 0.25, "boom"),
    ("s4_pete1", 4, "PETE", "So you're paid... to guess wrong... really fast.",
     "So you're paid... to guess wrong... really fast.", 1.3, "normal"),
    ("s4_zoe2", 4, "ZOE", "Until one time it's right.",
     "Until one time, it's right.", 0.3, "deadpan"),
    ("s4_riggy2", 4, "RIGGY", "I WROTE THE PAGE! I GET NEW COINS!",
     "I wrote the page! I get new coins!", 1.3, "boom"),
    # SCENE 5
    ("s5_pete1", 5, "PETE", "Well heck, I'd build a thousand Riggys!",
     "Well heck, I'd build a thousand Riggys!", 1.4, "shout"),
    ("s5_zoe1", 5, "ZOE", "Everybody does. So the game makes itself harder.",
     "Everybody does. So the game makes itself harder.", 0.9, "deadpan"),
    ("s5_zoe2", 5, "ZOE", "No matter how many miners show up, a new page still takes about ten minutes.",
     "No matter how many miners show up, a new page still takes about ten minutes.", 0.5, "deadpan"),
    ("s5_pete2", 5, "PETE", "So more diggers, same gold.",
     "So more diggers... same gold.", 0.3, "normal"),
    ("s5_zoe3", 5, "ZOE", "Exactly.",
     "Exactly!", 0.2, "deadpan"),
    ("s5_pete3", 5, "PETE", "That's the most honest thing I've heard in two hundred years.",
     "That's the most honest thing I've heard in two hundred years!", 0.5, "normal"),
    # SCENE 6
    ("s6_pete1", 6, "PETE", "And what does all this guessing cost?",
     "And what does all this guessing cost?", 1.2, "normal"),
    ("s6_zoe1", 6, "ZOE", "About as much electricity as a small country.",
     "About as much electricity as a small country.", 0.3, "deadpan"),
    ("s6_pete2", 6, "PETE", "A WHOLE COUNTRY? To play a guessing game?",
     "A WHOLE COUNTRY?! To play a guessing game?!", 0.35, "shout"),
    ("s6_riggy1", 6, "RIGGY", "ALSO I AM VERY HOT.",
     "Also... I am very hot.", 0.3, "boom"),
    ("s6_zoe2", 6, "ZOE", "Some people use the heat to warm greenhouses. We use it for this.",
     "Some people use the heat to warm greenhouses. We use it for this.", 1.1, "deadpan"),
    # SCENE 7
    ("s7_pete1", 7, "PETE", "How long till I win?",
     "How long till I win?!", 2.4, "shout"),
    ("s7_zoe1", 7, "ZOE", "With one little computer? Maybe a few thousand years.",
     "With one little computer? Maybe a few thousand years.", 0.3, "deadpan"),
    ("s7_pete2", 7, "PETE", "Ha! I spent forty years in a river. I'm basically warmed up.",
     "Ha! I spent forty years in a river. I'm basically warmed up!", 0.4, "normal"),
    # SCENE 8
    ("s8_pete1", 8, "PETE", "In my day, you dug for gold and mostly found nothing.",
     "In my day... you dug for gold. And mostly found nothing.", 1.6, "normal"),
    ("s8_zoe1", 8, "ZOE", "Now we guess for coins and mostly find nothing.",
     "Now we guess for coins, and mostly find nothing.", 0.3, "deadpan"),
    ("s8_pete2a", 8, "PETE", "...Well.",
     "Well.", 1.0, "normal"),
    ("s8_pete2b", 8, "PETE", "Good to know some things never change.",
     "Good to know some things never change.", 0.5, "normal"),
    ("s8_riggy1", 8, "RIGGY", "GAME OVER! INSERT ELECTRICITY TO CONTINUE!",
     "Game over! Insert electricity to continue!", 0.4, "boom"),
]

SPEAKER_COLOR = {"PETE": (255, 200, 40), "ZOE": (60, 232, 255), "RIGGY": (255, 70, 220)}
