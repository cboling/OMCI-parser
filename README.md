# ITU G.988 Parser for Code Generation

This directory contains a set of utilities for extracting information from an ITU G.988
OMCI documentation (currently .docx format only) and creating a data structure that
can be used to feed into a code generator.

Currently, this has only been tested against the Microsoft Word formatted version of
the November 2017 version of ITU G.966.  To my knowledge, the ITU only makes PDF copies
of this document available to the general public and you must be an ITU member to be
able to retrieve this document.

## Current Status

This is a work in progress.  Decode of several MEs has been performed but decode of all
possible is still in the works.

Currently, the final parser stage detects 317 ME Class ID Entries in the G.988 document
and can associate 220 of them with specific document sections.  There is a fair chance
that this is all that are actually defined by this version of the document. (See Item 1
of the **Future Work** section below).

## How To Run

There are currently two parsing stages in order to minimize debug time of the final stage
and this may help out in the future when attempting to support multiple document versions.

### Stage 1 - PreParsing

This stage extracts section table information from the input document and saves it
to an intermediate JSON file.  This stage takes from 3-5 minutes and typically should
only need to be ran once.

```bash
    usage: preParse.py [-h] [--input INPUT] [--output OUTPUT]
    
    optional arguments:
      -h, --help            show this help message and exit
      --input INPUT, -i INPUT
                            Path to ITU G.988 specification document
      --output OUTPUT, -o OUTPUT
                            Output filename, default: G.988.PreCompiiled.json
```

### Stage 2 - Final Parsing

This stage takes the pre-processed data from the first stage and peforms the final
deep parsing of the G.988 document.  Its output is a JSON file that describes the
basic structure of all the Managed Entities that are defined in the document.  This
output can then be feed into another program that is used to generate code that
can be used to encode & decode OMCI frames containing these managed entities.

```bash
    usage: parser.py [-h] [--ITU ITU] [--input INPUT] [--output OUTPUT]
                     [--classes CLASSES]
    
    optional arguments:
      -h, --help            show this help message and exit
      --ITU ITU, -I ITU     Path to ITU G.988 specification document
      --input INPUT, -i INPUT
                            Path to pre-parsed G.988 data, default:
                            G.988.PreCompiled.json
      --output OUTPUT, -o OUTPUT
                            Output filename, default: G.988.Parsed.json
      --classes CLASSES, -c CLASSES
                            Document section number with ME Class IDs, default:
                            11.2.4
```

***NOTE***: The second parser is currently being implemented and is not yet
fully functional.


## Remaining Items To Implement

The following items need to be done before this project can be demonstrated.

 - Create 'requirements.txt' 

 - Implement Jinja2 templates to convert the data definition into Golang Entity Types
 
 - Provide base OMCI encode/decode frame source code to use the code generated ME source
   files. (Target language: golang)
   
 - The 'Software Image' ME provides an extra set of attributes & actions. This needs to
   be compensated for.


## Future Work
 
 - Verify that all defined MEs are detected. The Class ID list in the G.988 document
   lists all IDs that have been defined, but the G.988 document only lists the ones that
   are valid for this specification. 
  
 - Support parsing previous/future versions of the ITU G.988 document. This will reuire
   that a few classes be modified to parse appropriately for a given document.
   
 - Support for parsing the AT&T OpenOMCI V3.0 specification if a .docx formatted document
   becomes available. If not, provide a hand-coded filter that can be applied against
   the appropriately parsed G.988 version to create appropriate output.
   
