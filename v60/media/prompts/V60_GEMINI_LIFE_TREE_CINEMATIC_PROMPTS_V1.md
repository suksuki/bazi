# V60 Gemini LifeTree Cinematic Prompts V1

Attach `web/public/assets/dream/v60-life-world-clean-v1.png` as the exact
composition reference for the first request. For every subsequent request,
also attach the approved final frame of the preceding clip.

## Shared scene and camera lock

```text
Use the attached V60 LifeTree image as an exact scene, camera and composition
lock. Preserve the same complete old LifeTree, trunk silhouette, branch
geometry, root-to-ground connection, distant mountains, grove, paper texture,
light direction, horizon, lens and crop. Do not regenerate or redesign the
tree. Do not move, bend, replace, thicken or remove branches. Keep all
interactive geometry registered to the source image.

Visual style is Eastern fairy-tale picture-book: luminous hand-painted
watercolor and gouache, restrained ink green, moss, mist gray, soft off-white
daylight and tiny muted antique-gold accents. Magic is quiet and material:
dew, paper fibers, reflected light and a very small amount of fine gold dust.
No neon, game reward glow, fantasy portal, explosive particles, glossy 3D,
anime, vector art or plastic rendering.

Camera is completely locked. No zoom, push-in, pan, tilt, parallax, focus
breathing, crop change or scene cut. Background remains stable except for
subtle localized leaf breathing and slow mist. No Abu, people, animals,
readable text, logo, UI, buttons, cards, diagrams or symbols.

Output 1920x1080, 24 fps, 8 seconds. Hold the first composition cleanly for
0.75 seconds and the final composition cleanly for at least 1.25 seconds for
Runtime handoff. Platform corner marks are tolerated only in empty peripheral
space and must not overlap the tree or semantic organ anchor.
```

The semantic organ anchor is one fixed point on the approved upper-right
living branch. In normalized source coordinates its center is approximately
`x=0.425, y=0.38`; the designer must confirm the same branch visually. Bud,
open flower and fruit must share this exact attachment point and occlusion.

## V60_TREE_01_FLOWER_BUD_APPEAR_V1

Append:

```text
ACTION: Begin with the exact clean LifeTree and no bud, no flower and no fruit.
At the fixed semantic organ anchor, a tiny natural swelling forms inside the
bark. Fine fibers and one short living stem emerge from the branch, followed
by a closed ivory-green flower bud. Growth is gradual, botanical and
physically attached behind the correct foreground twigs and leaves. A faint
warm reflection may travel only along the connected bark immediately before
the bud settles. End with one small closed bud, motionless and clearly rooted
to the branch.

Do not create additional buds, flowers, fruit, vines, UI markers or outcome
colors. Do not imply success, failure, fortune or danger.
```

## V60_TREE_02_FLOWER_OPEN_V1

Append:

```text
ACTION: Begin from the approved final frame containing the closed bud at the
same fixed anchor. The stem and branch do not move. The bud takes one quiet
breath, its sepals relax, and the petals unfold naturally into a restrained
ivory flower with a very soft antique-gold center. Use paper-fiber and dew
detail, not a bright magical burst. End with the flower fully open and stable
at exactly the same center, scale, stem angle and occlusion.

The open flower means only "the question is available". It must not reveal an
answer, majority direction, result, confidence or reward. No fruit is visible.
```

## V60_TREE_03_SHARED_FRUIT_SET_V1

Append:

```text
ACTION: Begin from the approved open-flower frame. After the AnswerSeal
collection is closed by Runtime, the petals fold inward and become a brief
veil of pale paper fibers. At the exact same branch anchor, one small
mist-white fruit forms around the flower center. The fruit is neutral,
unripe-looking and visually identical regardless of any submitted answer.
End with one sealed mist-white fruit attached to the same stem.

This is fruit set, not reveal or maturity. No opening, result light, color
grading, cracks, symbols, score, celebration or evidence appears.
```

## V60_TREE_04_FRUIT_MATURE_V1

Append:

```text
ACTION: Begin from the approved sealed mist-white fruit frame. World evidence
has now matured on the server. The fruit does not change color or size to
encode the result. Instead, its paper-fiber skin becomes slightly more
resolved, a single dew line settles, and the stem takes the weight naturally.
A quiet inner reflection appears and then becomes still. End with the same
closed fruit, now physically settled and ready to be opened by a later user
action.

Do not crack, open or reveal the fruit. Do not imply supported, partial or not
supported through hue, brightness, weather, particles or surrounding leaves.
```

## V60_TREE_05_FRUIT_OPEN_V1

Append:

```text
ACTION: Begin from the approved mature closed-fruit frame. Runtime has already
authorized Reveal. The fruit skin separates along one natural seam like
layered handmade paper, opening gently at the exact anchor. A restrained
neutral inner glow and a few fine antique-gold dust particles disperse into
the existing air, then fade. The branch and background remain unchanged. End
with a stable open fruit shell that leaves clean visual space for Runtime to
render the actual evidence and reconciliation.

The video itself must never contain or imply the answer. No words, icons,
charts, faces, colored result coding, fireworks, reward fanfare or judgment.
```

## Continuity acceptance

```yaml
camera_match: pixel_stable
tree_geometry_match: required
semantic_anchor_drift: zero_visible_drift
bud_flower_fruit_anchor: identical
fruit_before_seal: forbidden
result_coding_in_video: forbidden
runtime_evidence_in_video: forbidden
```
