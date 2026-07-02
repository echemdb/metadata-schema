**Added:**

* Added ``experimental.operationParameters`` describing how a measurement was
  operated: ``temperature`` (with active thermal control) and ``massTransport``
  with the forced-convection modes ``rotation`` (RDE/RRDE), ``flow``,
  ``ultrasound`` (sonoelectrochemistry) and ``stirring``. Each mode carries its
  defining quantity(ies) plus a ``control`` block referencing the controlling
  instrument by name.
* Added the ``ControlledQuantity``, ``Control``, ``MassTransport``,
  ``Rotation``, ``Flow``, ``Stirring`` and ``Ultrasound`` classes
  (``linkml/experimental/operation.yaml``).
* Added ``validate_instrument_references`` which checks that every
  ``operationParameters`` control block references an instrument that exists in
  the same ``experimental.instrumentation`` list. This cross-reference cannot
  be expressed in JSON Schema, so it is enforced during example validation.

**Changed:**

* ``Instrumentation.name`` is now the class ``identifier``; it is the key that
  ``operationParameters`` control blocks reference.

**Removed:**

* Removed ``temperature`` from ``system.electrolyte``; the temperature and its
  control now live under ``experimental.operationParameters.temperature``.

**Fixed:**

* Made ``update_expected_schemas`` output ASCII so it no longer crashes on
  Windows consoles using the cp1252 code page.
