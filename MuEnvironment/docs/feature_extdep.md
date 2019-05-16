# External Dependencies

## The Genesis

External dependencies started as we saw a need to no longer carry binary files in our code tree as it was causing bloat to our git version history.

It was also becoming troublesome to update binaries across branches and products. In addition, moving to a multi-repo world, it was becoming difficult to locate the binaries we needed to build a given product or platform.

## NuGet Dependency

NuGet is easy to understand, offers caching and authentication as well as being fairly platform and language agnostic.

## Web Dependency

Web dependency will download whatever is located at the source URL. It has three special fields:

### internal_path

This describes the internal structure of whatever we are downloading.

If you are just downloading a file, include the name you would like the file to be.

If you are downloading a directory, indicate so with a / before the path. The folder the path points to will have it's contents copied into the final name_ext_dep folder.

### compression_type

Including this field is indicating that the file being downloaded is compressed and that you would like the contents of internal_path to be extracted. If you have a compressed file and would not like it to be decompressed, omit this field.

Currently supports tar and zip. If the file is not compressed, omit this field.

### sha256

If desired, you can provide the hash of your file. This hash will be checked against what is being downloaded to ensure it is valid.

## How to use an ext_dep

An ext_dep is defined by a json file that ends in _ext_dep.json
It must follow the schema outlined below. It will be unpacked in a new folder in the same directory as the .json file in a folder named {name}_extdep.

We recommend adding any folder that ends in _extdep to your gitignore. It would look like this:

```.gitignore
*_extdep/
```

## The schema
From MU_BASECORE\BaseTools\Bin\iasl_ext_dep.json
```json
{
"scope": "corebuild",
"type": "nuget",
"name": "iasl",
"source": "https://api.nuget.org/v3/index.json",
"version": "20190215.0.0",
"flags": ["set_path", "host_specific"]
}
```
Unpacked in MU_BASECORE\BaseTools\Bin\iasl_extdep\

- Scope: See another doc about scopes
- Type: Right now nuget is the only supported type
- Name: This is the name of the ext_dep and will be part of the path where the nuget is unpacked
- Source: If you want to use your own NuGet index, you are welcome to
- Version: corresponds to the version on NuGet, which is three numbers seperated by periods.
- Flags: Optional conditions that can be applied, discussed later

## The Flags

There are specific flags that do different things. Flags are defined by MuEnviroment and cannot be modified without updating the pip module. More information on the flags can be found in the SDE documentation.

Another place to review is EnvironmentDescriptorFiles.py in Mu Environment

## How they work

Ext_deps are found by the SDE (self-describing environment). If you have any questions about that, go review the document for that. Once the ext_dep is found, it's unpacked by the logic in ExternalDependencies.py. Objects created with the data from ext_dep descriptors and are subclassed according to the "type" field in the descriptor. Currently, the only valid subclass is "nuget".

These objects contain the code for fetching, validating, updating, and cleaning dependency objects and metadata. When referenced from the SDE itself, they can also update paths and other build/shell vars in the build environment.

## Publishing a NuGet Package

There are several tutorials out there that discuss this exact topic, the Project Mu team have developed a few tools to make this process easier. Please refer to the NuGet Publishing doc in MU_BASECORE.
