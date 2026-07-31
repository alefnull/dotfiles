-- animations.lua
-- Animation curves and animation leaf settings

hl.config({
   animations = {
      enabled = false,
   },
})

hl.curve("overshot", { type = "bezier", points = { { 0.05, 0.9 }, { 0.1, 1.05 } } })
hl.curve("smoothIn", {
   type = "bezier",
   points = { { 0.25, 1.0 }, { 0.5, 1.0 } }
})
hl.curve("smoothOut", {
   type = "bezier",
   points = { { 0.05, 0.9 }, { 0.1, 1.05 } }
})
hl.curve("softSnap", {
   type = "bezier",
   points = { { 0.4, 0.0 }, { 0.2, 1.0 } }
})
hl.curve("fluent", {
   type = "bezier",
   points = { { 0.0, 0.0 }, { 0.2, 1.0 } }
})

hl.animation({
   leaf = "windows",
   enabled = true,
   speed = 3.0,
   bezier = "fluent",
   style = "slide",
})
hl.animation({
   leaf = "windowsIn",
   enabled = true,
   speed = 3.0,
   bezier = "fluent",
   style = "slide",
})
hl.animation({
   leaf = "windowsOut",
   enabled = true,
   speed = 3.0,
   bezier = "fluent",
   style = "slide",
})
hl.animation({
   leaf = "windowsMove",
   enabled = true,
   speed = 3.0,
   bezier = "overshot",
})
hl.animation({
   leaf = "layersIn",
   enabled = true,
   speed = 3.0,
   bezier = "smoothIn",
})
hl.animation({
   leaf = "layersOut",
   enabled = true,
   speed = 3.0,
   bezier = "smoothOut",
})
hl.animation({
   leaf = "fade",
   enabled = true,
   speed = 3.0,
   bezier = "smoothIn",
})
hl.animation({
   leaf = "fadeIn",
   enabled = true,
   speed = 3.0,
   bezier = "smoothIn",
})
hl.animation({
   leaf = "fadeOut",
   enabled = true,
   speed = 3.0,
   bezier = "smoothOut",
})
hl.animation({
   leaf = "fadeSwitch",
   enabled = true,
   speed = 3.0,
   bezier = "smoothIn",
})
hl.animation({
   leaf = "fadeShadow",
   enabled = true,
   speed = 3.0,
   bezier = "smoothIn",
})
hl.animation({
   leaf = "fadeDim",
   enabled = true,
   speed = 3.0,
   bezier = "smoothIn",
})
hl.animation({
   leaf = "fadeDpms",
   enabled = true,
   speed = 3.0,
   bezier = "smoothIn",
})
hl.animation({
   leaf = "fadeLayers",
   enabled = true,
   speed = 3.0,
   bezier = "softSnap",
})
hl.animation({
   leaf = "workspaces",
   enabled = true,
   speed = 3.0,
   bezier = "softSnap",
   style = "slidefadevert 50%",
})
hl.animation({
   leaf = "specialWorkspace",
   enabled = true,
   speed = 3.0,
   bezier = "fluent",
   style = "slidefadevert 50%",
})
