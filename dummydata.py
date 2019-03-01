def getDummy():
    GIFTCATEGORIES = ('fathersday', 'mothersday')
    GIFTITEMS = list()
    item1 = (
        "ME&YOU Soft Toy",
        "India",
        ("".join("https://rukminim1.flixcart.com/image/\
        704/704/jiyvvrk0/valentine-gift-set/s/h/q/\
        romantic-cycle-teddy-return-gifts-for-wife-\
        girlfriend-sister-on-original\
        -imaf6n52buppuxut.jpeg".split())),
        "2 Teddy, 1 Cycle",
        "570"
        )
    item2 = (
        "Buttercup Cute Sprinkles",
        "USA",
        ("".join("https://rukminim1.flixcart.com/image\
        /704/704/jle1qq80/stuffed-toy/d/q/s/\
        cute-bootsy-purple-122-cm-huggable-and-\
        loveable-for-someone-original-\
        imaf6geqkbwfgmxh.jpeg".split())),
        "1 Taddy Bear,Ideal For Girls",
        "600"
        )
    GIFTITEMS.extend([item1, item2])
    return GIFTCATEGORIES, GIFTITEMS
