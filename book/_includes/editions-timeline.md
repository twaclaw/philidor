<!-- The timeline drawing for editions.qmd. Kept apart so the chapter
     stays prose; it is included inline, which is what lets the detail
     panel and the theme reach into it. -->

```{=html}
<figure class="editions-figure">
<svg viewBox="0 0 880 250" role="img" width="100%"
     aria-label="Timeline of the editions of Philidor's Analysis, 1749 to 1819,
     on two lines of descent: French above, English below.">
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5"
            markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" class="ed-arrowhead"/>
    </marker>
  </defs>

  <text x="6" y="52" class="ed-lane">FRENCH</text>
  <text x="6" y="192" class="ed-lane">ENGLISH</text>

  <path d="M120 104 L120 62 L318 62" class="ed-flow" marker-end="url(#arrow)"/>
  <path d="M120 144 L120 186 L318 186" class="ed-flow" marker-end="url(#arrow)"/>
  <path d="M442 62 L716 62 L716 73" class="ed-flow" marker-end="url(#arrow)"/>
  <path d="M442 186 L520 186" class="ed-flow" marker-end="url(#arrow)"/>

  <g class="ed-node" tabindex="0" data-year="1749"
     data-name="L&#39;Analyze des Echecs"
     data-detail="Philidor&#39;s first edition, written in London and printed in
       French. Three printings carry the date. Nine games with their back-games,
       and the ends of parties. Its rule on promotion was stricter than what
       followed: a pawn could be exchanged only for a piece already captured.
       No publisher is named, and catalogues record the London imprint as
       false -- the book was probably printed in Paris.">
    <title>Point at this edition for its full imprint.</title>
    <rect x="62" y="99" width="116" height="50" rx="3"/>
    <text x="120" y="117" class="ed-title">1749</text>
    <text x="120" y="130" class="ed-sub">L&#39;Analyze</text>
    <text x="120" y="143" class="ed-pub">no publisher</text>
  </g>

  <g class="ed-node" tabindex="0" data-year="1777"
     data-name="Analyse du jeu des echecs"
     data-detail="Nouvelle edition, considerablement augmentee. The French
       branch of the rewriting, published the same year as the English one. It
       is this line that Kenny would translate from forty years later. Like the
       1749 it names no publisher, and its imprint is likewise catalogued as
       false.">
    <title>Point at this edition for its full imprint.</title>
    <rect x="322" y="37" width="120" height="50" rx="3"/>
    <text x="382" y="55" class="ed-title">1777</text>
    <text x="382" y="68" class="ed-sub">Analyse</text>
    <text x="382" y="81" class="ed-pub">no publisher</text>
  </g>

  <g class="ed-node ed-base" tabindex="0" data-year="1777"
     data-name="Analysis of the Game of Chess"
     data-detail="A new edition, greatly enlarged. London: printed for
       P. Elmsley, in the Strand. Booksellers call it possibly the first
       chess book published in
       English. It reprints the 1749 material with corrections and adds the
       supplement, the Gambit of Salvio, the ends of parties, and seventeen
       rules of the game."
     data-mark="base"
     data-role="The base text of this transcription: all 96 games here are
       read from a scan of it.">
    <title>Point at this edition for its full imprint.</title>
    <rect x="322" y="161" width="120" height="50" rx="3"/>
    <text x="382" y="179" class="ed-title">1777</text>
    <text x="382" y="192" class="ed-sub">Analysis</text>
    <text x="382" y="205" class="ed-pub">P. Elmsley</text>
  </g>

  <g class="ed-node ed-collated" tabindex="0" data-year="1790"
     data-name="Analysis of the Game of Chess"
     data-detail="A new edition, improved and greatly enlarged, in two volumes,
       adding games the author played blindfold against three adversaries.
       London: printed for P. Elmsly, in the Strand. It renames the 1777
       supplement as a series of Regular Parties."
     data-mark="collated"
     data-role="Collated against here, but only volume I is to hand — the
       parties and gambits. Volume II held the ends of parties, which is why
       chapters 70 to 98 have never been read against a second source.">
    <title>Point at this edition for its full imprint.</title>
    <rect x="524" y="161" width="120" height="50" rx="3"/>
    <text x="584" y="179" class="ed-title">1790</text>
    <text x="584" y="192" class="ed-sub">Analysis</text>
    <text x="584" y="205" class="ed-pub">P. Elmsly</text>
  </g>

  <g class="ed-node ed-yours" tabindex="0" data-year="1819"
     data-name="Analysis of the Game of Chess, by W. S. Kenny"
     data-detail="Illustrated by diagrams, on which are marked the situation of
       the party for the back-games and ends of parties; with critical remarks
       and notes by the author of the Stratagems of Chess. Translated from the
       last French edition and further illustrated with notes by W. S. Kenny
       (William Stopford Kenny, 1788–1867), author of Practical Chess Grammar.
       London: printed for T. and J. Allman, Prince&#39;s Street,
       Hanover-Square; and sold by Baldwin, Cradock and Joy, Paternoster Row;
       and Bell and Bradfute, Edinburgh. Carries seventeen rules, as the 1777
       does."
     data-mark="yours"
     data-role="The beautiful physical edition I have, and the copy this
       transcription is compared against.">
    <title>Point at this edition for its full imprint.</title>
    <rect x="656" y="73" width="120" height="50" rx="3"/>
    <text x="716" y="91" class="ed-title">1819</text>
    <text x="716" y="104" class="ed-sub">Kenny</text>
    <text x="716" y="117" class="ed-pub">T. &amp; J. Allman</text>
  </g>

  <g class="ed-key">
    <rect x="62" y="222" width="12" height="12" rx="2" class="ed-swatch-base"/>
    <text x="80" y="232">transcribed here</text>
    <rect x="216" y="222" width="12" height="12" rx="2" class="ed-swatch-collated"/>
    <text x="234" y="232">collated against</text>
    <rect x="368" y="222" width="12" height="12" rx="2" class="ed-swatch-yours"/>
    <text x="386" y="232">the beautiful physical copy I have</text>
    <text x="874" y="232" class="ed-hint">point at any edition for its full imprint &#8595;</text>
  </g>
</svg>

<div class="edition-detail" data-empty="Point at an edition to read its imprint.">
  <p class="edition-detail__head"></p>
  <p class="edition-detail__body">Point at an edition to read its imprint.</p>
  <p class="edition-detail__role"></p>
</div>

<figcaption>Two lines of descent from 1749. This transcription follows the
English one; a copy translated from the French descends by the other path, and
the two had been apart for forty years by 1819.</figcaption>
</figure>
```
