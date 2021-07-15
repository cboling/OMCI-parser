# ITU G.988 Parser for Code Generation

This directory contains a set of utilities for extracting information from an ITU G.988
OMCI documentation (currently .docx format only) and creating a data structure that
can be used to feed into a code generator for the purpose of creating object to
model the managed entities in OMCI.

Currently, this has only been tested against the Microsoft Word formatted version of
the November 2017 version of ITU G.966.  To my knowledge, the ITU only makes PDF copies
of this document available to the general public and you must be an ITU member to be
able to retrieve this document.

## Current Status

The parser has is now fairly mature and can decode over 180 Managed Entity definitions. The
preparsing stage detects 319 ME Class ID Entries in the 2020 ITU G.988 document
and can associate 228 of them with specific document sections.  There is a fair chance
that this is all that are actually defined by this version of the document. (See Item 1
of the **Future Work** section below).

One significant item of note is that the downloaded 3/2020 version of the ITU G.988 document
has revision tracking on and the current **docx** python package cannot examine the new
revisions that have not been accepted for some existing Managed Entities.  It is strongly
suggested that you open the document in work and perform a 'Accept All Changes'
command to insure that you pick up the new changes.  Do not use the option that turns off
revision tracking because after accepting the ITU revisions, if you should accidentally modify
the document, it will not affect parsing.  Sort of a nice 'feature/bug' of **docx** that
we can make use of.


## How To Run

There are a number of steps to perform in order to generate code from the ITU Document
(Microsoft Word format).  I currently use the 3/2020 version but have not added that
document to this repo since it is available only if you have an ITU TIES loging and I
did not want to violate any privacy policies.  If anyone knows if it is okay to distribute
this document via the repo, please point me to the proper place on the ITU website
stating that policy and I will be happy to share it.

The steps to run it are:

  1. Pre-parse the G.988 Word Document via 'preParse.py' to create the 'G.988.Precompiled.json' file
  2. Parse the G.988 JSON via 'parser.py' to create the G.988.Parsed.json file.  At this point,
     there is just a minimal fragment 'G.988.augment.yaml' file that really as a little bit of data
  3. Run the 'augmentGenerator.py' file to create an 'augmented.yaml' file in the 'metadata' sub-
     directory. This will have all the newly parsed JSON converted to YAML form.
  4. Hand edit the augmented.yaml file by hand and adjust the values as needed.  Once you are done,
     overwrite the base directory's 'G.988.augment.yaml' file with this.  You now have a
     metadata file that will be used everytime you either run the parser (or code generator) with
     you updated metadata.
  5. Run the 'parser.py' program again. This will pick up the metadata hint you created in step 4
     and will create an updated 'G.988.Parsed.json' file with your data.
  6. Run either the C or Go code generator to generate your classes. (only the Go code generator
     is public at this time)

### Stage 1 - PreParsing

This stage extracts section table information from the input document and saves it
to an intermediate JSON file.  This stage takes from 3-5 minutes and typically should
only need to be ran once.

```bash
    usage: preParse.py [-h] [--input INPUT] [--output OUTPUT]
    
    optional arguments:
      -h, --help            show this help message and exit
      --input INPUT, -i INPUT
                            Path to ITU G.988 specification document, default T-REC-G.988-202003-I!Amd3!MSW-E.docx
      --output OUTPUT, -o OUTPUT
                            Output filename, default: G.988.PreCompiiled.json
```

### Stage 2 - Initial Parsing

This stage takes the pre-processed data from the first stage and performs the final
deep parsing of the G.988 document.  Its output is a JSON file that describes the
basic structure of all the Managed Entities that are defined in the document.  This
output can then be feed into another program that is used to generate code that
can be used to encode & decode OMCI frames containing these managed entities.  This stage
can also accept a metadata.yaml file that can be used to provide customized attributes
to the output JSON such as constraints.

```bash
    usage: parser.py [-h] [--ITU ITU] [--input INPUT] [--output OUTPUT]
                     [--classes CLASSES]
    
    optional arguments:
      -h, --help            show this help message and exit
      --ITU ITU, -I ITU     Path to ITU G.988 specification document, default:
                            T-REC-G.988-202003-I!Amd3!MSW-E.docx
      --input INPUT, -i INPUT
                            Path to pre-parsed G.988 data, default:
                            G.988.PreCompiled.json
      --output OUTPUT, -o OUTPUT
                            Output filename, default: G.988.Parsed.json
      --classes CLASSES, -c CLASSES
                            Document section number with ME Class IDs, default:
                            11.2.4
      --hints INPUT, -H INPUT
                            Path to a hand nodified G.988 input data file to augment the
                            parser. default: G.988.augment.yaml
```

#### Stage 3 - Augment Generation (Optional)

This step takes the output of Stage 2 and creates an output YAML file that can be
hand modified to feed back into the Stage 2 parser to create a more customized
output. YAML was chosen since it supports commenting and can be a bit easier to
read at times. The two main purposes of this file is to provide default values
for each attribute (parser not smart enough and ITU does not provide all of them)
and to provide constraints (same parser/ITU comment as before). 

The way the augment file works in a Stage 2 re-run is that as the parser is parsing
a particular ME Class ID, it will look for the values first in the Augmented YAML input,
and then the ITU document. This allows for most any field to be customized via the
YAML input, but I would suggest only supplying the bare minimum of changes as work
on the parser will continue to improve over time. The default values and constraints
will probably never get much better, so that is why I mentioned them as good targets.

At the top of the augmentGenerator.py file are a list of class IDs I personally am
most interested in for my purposes. Feel free to add your own. Should I have time in
the future, may provide a command line option to specify these IDs.

```bash
    usage: augmentGenerator.py [-h] [--ITU ITU] [--input INPUT] [--output OUTPUT]
                     [--classes CLASSES]
    
    optional arguments:
      -h, --help            show this help message and exit
      --input INPUT, -i INPUT
                            Path to parsed G.988 data, default:
                            G.988.Parsed.json
      --output DIR, -o DIR
                            Output dirctory to place the generated YAML file, default:
                            metadata
      --existing YAML, -e YAML
                            Existing Augment YAML file to append too. default:
                            G.988.augment.yaml
```

#### Parsed output format

The following is an example of the JSON structure output by the second stage that
can be used by a code generator to extract additional information out of the ITU
G.988 document.  Note that not all output has been verified as accurate and support
for attribute sizes is not yet implemented.

The output is a JSON dictionary with the key being the ME class ID and the data
the decoded ME Class information. This information is composed of the following
sections:

```json
{
  "2": {
    "class_id": 2,
    "name": "ONU data",
    "section": {
      "title": "ONU data",
      "number": "9.1.3"
    },
    "description": [ 919, 920, 922 ],
    "relationships": [],
    "actions": [
      "Set",
      "Get",
      "GetAllAlarms",
      "GetAllAlarmsNext",
      "MibUpload",
      "MibUploadNext",
      "MibReset"
    ],
    "optional_actions": [],
    "attributes": {
      "0": {
        "name": "Managed Entity  Id",
        "description": [ 924, 924 ],
        "access": [ "Read" ],
        "optional": false,
        "size": 0,
        "avc": false,
        "tca": false
      },
      "1": {
        "name": "Mib Data Sync  ",
        "description": [ 925, 925 ],
        "access": [ "Read", "Write" ],
        "optional": false,
        "size": 0,
        "avc": false,
        "tca": false
      }
    },
    "alarms": {},
    "avcs": {},
    "test_results": {},
    "hidden": false
  },
  ...
```

### Stage 5 - Code Generation

The third stage is to generate source code. In the first implementation, go-lang
will be the target language. There is a companion Go project related to this parser
[OMCI](https://github.com/cboling/omci) that supplies several base types and
constants that this code generator uses and will consume the Go generated code.

To generate Go code, use the following command:
```bash
    usage: goCodeGenerator.py [-h] [--ITU ITU] [--input INPUT] [--dir DIRECTORY]
                     [--force]
    
    optional arguments:
      -h, --help            show this help message and exit
      --ITU ITU, -I ITU     Path to ITU G.988 specification document. Default:
                            T-REC-G.988-202003-I!Amd3!MSW-E.docx
      --input INPUT, -i INPUT
                            Path to parsed G.988 data, default:
                            G.988.parsed.json
      --dir DIRECTORY, -d DIRECTORY
                            Output directory for generated source code,
                            default: 'generated'
      --force, -f           Force overwrite of any existing output directory, by
                            default, the program will not touch any existing directory
                            or source code. This flag will delete the output directory
                            and install new code-generated files.
```

## Remaining Items To Implement

The following items need some work or attention:
   
 - The 'Software Image' ME provides an extra set of attributes & actions. This needs to
   be compensated for.
   
 - Use of the AVC and/or Alarm parsed tables need to be incorporated into the code
   generation phase.


## Future Work
 
 - Verify that all defined MEs are detected. The Class ID list in the G.988 document
   lists all IDs that have been defined, but the G.988 document only lists the ones that
   are valid for this specification. 
  
 - Support parsing previous/future versions of the ITU G.988 document. This will require
   that a few classes be modified to parse appropriately for a given document. For now,
   I would suggest using the augment feature. This is useful to pull in a few changes from
   the two existing G.988 admendments.

   
