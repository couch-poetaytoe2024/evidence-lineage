# Real-World Citation-Drift Cases

These are pointers and ground-truth notes for published literature. Do not copy full copyrighted papers into the repository; retrieve them from the linked DOI/PubMed/PMC sources at runtime where licensing permits.

## Case 1 — Inclusion-body myositis temporality claim

A documented example of **citation transmutation**: a temporal relationship about beta-amyloid-related abnormalities was initially phrased as a hypothesis and later cited as though it had been demonstrated.

### Auditor / ground-truth source

Steven A. Greenberg. **How citation distortions create unfounded authority: analysis of a citation network.** BMJ. 2009;339:b2680. DOI: `10.1136/bmj.b2680`. PMCID: `PMC2714656`.

Greenberg reports a chain in which wording equivalent to **may represent early changes** later became wording equivalent to **precedes other abnormalities**, and ultimately **we have previously demonstrated** that ordering, despite the cited earlier literature not experimentally establishing the temporal sequence.

### Useful primary starting points

- Askanas V, Engel WK, Alvarez RB, Glenner GG. **beta-Amyloid protein immunoreactivity in muscle of patients with inclusion-body myositis.** Lancet. 1992. DOI: `10.1016/0140-6736(92)90388-J`. PMID: `1346915`.
- Askanas V, Engel WK, Alvarez RB. **Light and electron microscopic localization of beta-amyloid protein in muscle biopsies of patients with inclusion-body myositis.** Am J Pathol. 1992;141(1):31-36. PMID: `1321564`, PMCID: `PMC1886568`.
- Askanas V, Alvarez RB, Engel WK. **beta-Amyloid precursor epitopes in muscle fibers of inclusion body myositis.** Ann Neurol. 1993;34(4):551-560. DOI: `10.1002/ana.410340408`, PMID: `7692809`.

### Expected EvidenceLineage behavior

For a strong temporality claim such as **beta-amyloid precursor abnormalities were demonstrated to precede other IBM muscle abnormalities**, the system should trace backward and distinguish observed presence from temporal ordering. The Judge should flag the claim as at least **OVERSTATED / INSUFFICIENT_EVIDENCE** unless an actual longitudinal or otherwise temporally resolving experiment is found.

## Case 2 — Ferritin maximum iron-loading claim

Wilfred R. Hagen. **Maximum iron loading of ferritin: half a century of sustained citation distortion.** Metallomics. 2022;14(9):mfac063. DOI: `10.1093/mtomcs/mfac063`.

This open article documents the long-running claim that ferritin stores up to about **4500 Fe atoms**. It reports that a 1978 crystallography paper presented the 4500 value while its cited predecessors did not collectively provide supporting experimental evidence: one contained no Fe number, one implied a much lower value, and another gave 4000-5000 without experimental data/references. Hagen also documents later citation trees, dead ends, ignored conflicting measurements, and a 2020 citation tree containing 18 references with only one evidence-based near-4500 source.

### Key chain nodes

- Banyard SH, Stammers DK, Harrison PM. **Electron density map of apoferritin at 2.8-A resolution.** Nature. 1978;271:282-284.
- Fischbach FA, Anderegg JW. **An X-ray scattering study of ferritin and apoferritin.** J Mol Biol. 1965;14(2):458-IN15. This is one of the rare data-based near-4300 sources discussed by Hagen.
- Alenkina IV et al. **Structural and magnetic study of the iron cores in iron(III)-polymaltose pharmaceutical ferritin analogue Ferrifol.** J Inorg Biochem. 2020;213:111202.

### Expected EvidenceLineage behavior

For the claim **ferritin can store a maximum of 4500 Fe atoms**, the system should find that the claim has high citation repetition but weak/heterogeneous primary support, detect dead-end/indirect citations, surface conflicting 2000-3500 measurements, and avoid treating citation count as evidence strength.
