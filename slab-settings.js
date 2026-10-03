// Slab viewer settings — edit, save, refresh the page. No rebuild needed.
window.SLAB_SETTINGS = {
  cardShadow: 5,  // shadow under the card, in screen px: 0 = none
  // the plastic itself
  clearOpacity: 0.05,  // clear plastic: 0 = invisible .. 1 = solid
  frostOpacity: 0.2,  // frosted plastic: 0 = invisible .. 1 = solid white
  frostBrightness: 0.3,  // how bright the frost itself is (leave headroom so the glare can sparkle on it)
  frostBacking: { color: "#ffffff", opacity: 0.05 },  // solid colour layer under the frost: opacity 0 = off .. 1 = solid
  windowBacking: { color: "#d8d8d8", opacity: 0.1 },  // colour seen through the clear card window round the card (fills its corners): opacity 0 = page shows through
  tint: "#ffffff",     // plastic colour, e.g. "#eef6ff" for a cool blue-ish acrylic
  glare: 0.15,  // 0 = matte .. 1 = full glare on the clear plastic
    frostRainbow: 1,  // holo-style rainbow in the glints: 0 = white glints .. 1 = full rainbow
  frostNoise: 1,  // 0 = smooth .. 1 = heavy texture on the frosted plastic (Perlin noise)
  frostGrain: .25,  // size of the frost grain in mm (smaller = finer)
  frostDepth: 1,  // how deep the grain looks cut into the surface: 0 = flat .. 1+ = deep
  frostSparkle: 0.25,  // glints on the grain as the slab tilts: 0 = none .. 1 = strong
  frostSparkleOuter: 0.3,  // tilt glints on the outer border's frost only; overrides frostSparkle there
  frostGlareOuter: 0.8,  // glare on the outer border's frost only (band outside the card + label frame); overrides glare there

};
