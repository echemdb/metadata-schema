**Added:**

* Added a shared ``PreparationProcedure`` class (``linkml/general/preparation_procedure.yaml``) with ``url`` and a step-by-step ``description`` list, used by electrodes, the electrochemical cell, and the electrolyte.
* Added ``preparationProcedure`` to each entry of ``system.electrolytes`` to describe how the electrolyte was prepared, e.g., purification or degassing.
* Added a migration step that converts ``system.electrochemicalCell.cleaningProcedure`` into ``system.electrochemicalCell.preparationProcedure.description`` (run ``mdstools update``).

**Changed:**

* Changed ``system.electrochemicalCell.cleaningProcedure`` (free-text string) to ``system.electrochemicalCell.preparationProcedure`` (``PreparationProcedure`` object), following the structure of the electrodes (see #128). This is a breaking change.
* Changed the name of the ``ElectrodePreparation`` class to ``PreparationProcedure``; the structure of ``electrodes[].preparationProcedure`` is unchanged.

**Removed:**

* Removed ``system.electrochemicalCell.cleaningProcedure``; existing files are upgraded by the migration.
