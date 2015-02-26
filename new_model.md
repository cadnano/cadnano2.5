# Objects names need to change

* `Strand` --> Oligo (subclass `ProxyObject`): this is single a stranded piece of DNA
* `StrandSet` --> `OligoList` or `OligoSet` (subclass `ProxyObject`) (an linear ordered list / hybrid datastructure
                 of `OligoInstance`s)

* `VirtualHelix` --> `VirtualHelix` (subclass `ProxyObject`).  A spatial origin for `PartList`s and container for
    references to its `PairedPartInstance`s

* `Oligo` --> `Strand` (subclass `ProxyObject`) and ordered list of `StrandInstances` or `OligoInstance`s

* `Part` --> `Block` (name debatable) (subclass `AbstractAssembly`)
    Blocks are really just a subclass of assembly where virtual helices can live

* `Assembly` --> `Assembly` (subclass `AbstractAssembly`)
  * Can be assemblies of assemblies
  * Can be multiple assemblies per virtualhelix
  * Can be collections of virtualhelices


# NEW STUFF

* `AbstractAssemblyInstace` (subclass `ObjectInstance`)

* `OligoInstance` (subclass `ObjectInstance`) --> Pointer to a part or all of another `Oligo` / `OligoInstance`.
  * offset
  * length

* `Part` (subclass `AbstractAssembly`) --> assembly containing 2 arrays containing 0 or more `OligoInstance`s or `StrandInstances` paired with each other
    
* `PartInstance` (subclass `AbstractAssemblyInstance`)

   When you import a plasmid and want to reference a piece of it you get:

  * 1 `Part`
  * 1-2 `PartInstances` (depending whether you wat single or double stranded)

   And you place a `PartInstance` onto a `VirtualHelix` of a `Block`

  * You get all of the features that overlap the reference region

   If you want to break the share link, you create a new:

  * `Part`
  * `PartInstance`
  * 1 or 2 `Oligo`s or `Strand`s (Depending on whether you want to edit one or both `Oligo`s)
  * 1 or 2 `OligoInstance`s (etc) or `StrandInstance`s


Every Type of object can have features/annotations
