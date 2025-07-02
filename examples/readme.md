This section contains descriptors that are used to describe an electrochemical resource in a tabular-data-package.
* [curation](curation.yaml): Details on the curation process
* [eln](eln.yaml): URL to an electronic lab notebook
* [experimental](experimental.yaml): Descriptor supporting `system.yaml`, e.g., contains a list of instrument.
* [figureDescription](figure_description.yaml): contains mainly axis properties.
* [project](project.yaml): List of projects related to the source data.
* [source](source.yaml): Source of published data.
* [system](system.yaml): Details describing the experimental vessel.

Some of the descriptors are mandatory, while other optional descriptors depend on origin of the data. For example it is very unlikely that there exists an ELN entry of data published in the sixties.

## Recording raw data

The experimentalist is encouraged to record the following descriptors along with raw data:

<!-- TODO: Add link and description to autotag-metadata -->
* [curation](curation.yaml)
* [eln](eln.yaml)
* [experimental](experimental.yaml)
* [figureDescription](figure_description.yaml)
* [project](project.yaml)
* [system](system.yaml)

## Submission to echemdb/website

Data for the [echemdb/website]() can be submitted as a datapackage (JSON) and CVS, YAML and SVG or YAML and CSV.
In any case the files should be named:
`Author_YYYY_FirstTitleWord_Page_fignr_identifier` such as `mustermann_2022_electrochemical_1345_1b_solid`. The name should be lower case.

**Submitting a YAML with an SVG**
The YAML must contain the following descriptors:

* [curation](curation.yaml)
* [experimental](experimental.yaml)
* [source](source.yaml)
* [system](system.yaml)

**Submitting a YAML with a CSV**

* [curation](curation.yaml)
* [experimental](experimental.yaml)
* [figureDescription](figure_description.yaml)
* [source](source.yaml)
* [system](system.yaml)  
