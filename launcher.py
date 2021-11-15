"""idleminer launcher"""

if input("Launch story mode?").lower().startswith("n"):
    import idleminer
    idleminer.main()
else:
    import story
    story.main()
