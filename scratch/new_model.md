# Objects names need to change

* `Strand` --> `VirtualPathNode`  (subclass `ProxyObject`): a reference to a 
piece of a StrandNodeInstance mapping "Strand Space" onto "Path Space".  It has
 indices into the strandnodeinstance, as well as indices into the VirtualStrand.  
"PathNode" could maybe use a better word than Path.  It still maintains the 
pointers to 5p and 3p `VirtualPathNodes`

* `StrandSet` --> `VirtualStrand` (subclass `ProxyObject`) (an linear ordered 
list / hybrid datastructure of `OligoInstance`s)

* `VirtualHelix` --> `VirtualHelix` (subclass `ProxyObject`).  A spatial origin 
for `VirtualStrand`s and container for references to its `PartInstance`s

* `Oligo` --> `StrandNode`/`StrandNodeInstances` (subclass `ProxyObject`) an 
ordered list of 0 or more : this is single a stranded piece of DNA,  It's a 
tree like data structure where at each level
    a `StrandNodeInstance` and possibly a `StrandNode` need to be created

* `Part` --> `Block` (name debatable) (subclass `AbstractAssembly`)
    Blocks are really just a subclass of assembly where virtual helices can live

* `Assembly` --> `Assembly` (subclass `AbstractAssembly`)
  * Can be assemblies of assemblies
  * Can be multiple assemblies per virtualhelix
  * Can be collections of virtualhelices


# NEW STUFF

* `AbstractAssemblyInstance` (subclass `ObjectInstance`)

* `Part` (subclass `AbstractAssembly`) --> assembly containing 2 arrays 
containing 0 or more `StrandNodes`
    
* `PartInstance` (subclass `AbstractAssemblyInstance`).  Points to 
`StrandNodeInstances` of a 2 `StrandNodes`

   When you import a plasmid and want to reference a piece of it you get:

  * 1 `Part`
  * 1-2 `PartInstances` (depending whether you want single or double stranded)

   And you place a `PartInstance` onto a `VirtualHelix` of a `Block`

  * You get all of the features that overlap the reference region

   If you want to break the share link, you create a new:

  * `Part`
  * `PartInstance`
  * 1 or 2 `StrandNodes`s (Depending on whether you want to edit one or both `StrandNodes`s)
  * 1 or 2 `StrandNodeInstance`s


Every Type of object can have features/annotations
