**Added:**

* Added a required ``name`` to each entry of ``system.electrolytes``, unique within the list and preferably descriptive, e.g. ``KOH``, ``HClO4``, or ``catholyte`` and ``anolyte`` in a divided cell. (#129)

**Changed:**

* Changed the single ``system.electrolyte`` object to the list ``system.electrolytes`` with at least one entry, so that systems with several electrolytes, such as divided cells (H-cells, membrane electrolysers) with catholyte and anolyte, can be described. This is a breaking change; run ``mdstools update`` to migrate existing files, which turns the old electrolyte into a single entry named ``electrolyte1``; replace it with a descriptive name such as ``KOH`` where possible. (#129)