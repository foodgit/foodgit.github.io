#converts metric amounts in recipe text to freedom units for the freedom edition of the book
#the site does the same in the browser, keep the rules in sync with assets/js/units.js
import math, re

GLYPHS = {'½': .5, '¼': .25, '¾': .75, '⅓': 1/3, '⅔': 2/3, '⅛': .125}
EIGHTHS = ['', '⅛', '¼', '⅜', '½', '⅝', '¾', '⅞']
NUMBER = r'(?:\d+(?:\.\d+)?(?:\s?[½¼¾⅓⅔⅛])?|[½¼¾⅓⅔⅛])'
AMOUNT = re.compile(r'(?<![\w.])(' + NUMBER + r')(?:(\s?(?:-|–|to)\s?)(' + NUMBER + r'))?(\s?)(°C|kg|g|ml|litres?|liters?|cm|mm|l)(?![A-Za-z])')

def value(text):
    #1, 1.5, 1½, 1 ½ or ½ as a number
    match = re.match(r'(\d+(?:\.\d+)?)?\s?([½¼¾⅓⅔⅛])?$', text)
    return float(match[1] or 0) + GLYPHS.get(match[2], 0)

def nearest(x, step):
    return math.floor(x / step + .5) * step

def show(x):
    #multiples of an eighth as 5½, ¾ and so on
    whole, part = divmod(int(round(x * 8)), 8)
    return (str(whole) if whole else '') + EIGHTHS[part]

def weight(grams):
    oz = grams / 28.3495
    if oz < 16:
        return show(max(nearest(oz, .5 if oz >= 4 else .25), .25)) + ' oz'
    whole = round(oz)
    pounds, ounces = divmod(whole, 16)
    return str(pounds) + ' lb' + (' ' + str(ounces) + ' oz' if ounces else '')

def volume(ml):
    if ml >= 1000:
        return show(nearest(ml / 946.353, .25)) + ' qt'
    fl = ml / 29.5735
    return show(max(nearest(fl, .5 if fl >= 1 else .25), .25)) + ' fl oz'

def length(mm):
    inches = mm / 25.4
    step = .125 if inches < 1 else .25 if inches < 4 else .5
    return show(max(nearest(inches, step), .125)) + ' in'

def temperature(celsius):
    f = celsius * 9 / 5 + 32
    return str(int(nearest(f, 25 if f >= 250 else 5))) + '°F'

#unit: (to base value, formatter), base is g, ml, mm or °C
CONVERSIONS = {
    '°C': (1, temperature), 'g': (1, weight), 'kg': (1000, weight),
    'ml': (1, volume), 'l': (1000, volume), 'litre': (1000, volume), 'litres': (1000, volume),
    'liter': (1000, volume), 'liters': (1000, volume), 'cm': (10, length), 'mm': (1, length),
}

def convert(match):
    first, between, second, space, unit = match.groups()
    if unit == 'l' and space:
        return match[0]
    factor, fmt = CONVERSIONS[unit]
    if second is None:
        return fmt(value(first) * factor)
    return fmt(value(first) * factor) + between + fmt(value(second) * factor)

def to_freedom(text):
    return AMOUNT.sub(convert, text)

if __name__ == '__main__':
    import sys
    sys.stdout.write(to_freedom(sys.stdin.read()))
