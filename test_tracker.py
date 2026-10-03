from tracker import title_ok

assert title_ok("1997 POKEMON JAPANESE FOSSIL #151 MEW-HOLO PSA 9")
assert title_ok("1997 Pokemon Japanese Fossil Holo #151 Mew - PSA MINT 9")
assert not title_ok("1997 Pokemon Japanese Fossil Holo Mew #151 PSA 10 GEM MINT")
assert not title_ok("Japanese Fossil Mew PSA 9.5")
assert not title_ok("1997 Pokemon Japanese Fossil Holo Mew #151 PSA 8 NM-MT")
assert not title_ok("1999 Pokemon Fossil Mew Holo PSA 9")  # English, not Japanese
assert not title_ok("CGC 9 MINT Mew Fossil Japanese")
assert title_ok("Pokémon Mew 151 Mystery of the Fossils Holo Rare PSA 9 1997 Japanese TCG")
assert not title_ok("ANCIENT MEW PSA 9 POKEMON PROMO MEWTWO STRIKES BACK MOVIE JAPANESE")
assert not title_ok("PSA 9 Pokemon Card Mew ex SAR 347/190 Alt Art SV4a Shiny Treasure Japanese Holo")
print("ok")
