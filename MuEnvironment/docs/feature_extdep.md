# External Dependencies

## The Genesis

External dependencies started as we saw a need to no longer carry binary files in our code tree as it was causing bloat to our git version history.

It was also becoming troublesome to update binaries across branches and products. In addition, moving to a multi-repo world, it was becoming difficult to locate the binaries we needed to build a given product or platform.

## Why NuGet

As of writing (April 2019), we only support resolving nuget dependencies, though this is easy to extend and we are considering other options. We picked NuGet as it's easy to understand, offers caching and authentication as well as being fairly platform and language agnostic.

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
