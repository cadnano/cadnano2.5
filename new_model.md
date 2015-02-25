# Objects names need to change

Strand --> Part (subclass ProxyObject): this is single a stranded piece of DNA
StrandSet --> PartList or PartSet (subclass ProxyObject) (an ordered list / hybrid datastructure
                 of PartInstances)

VirtualHelix --> VirtualHelix (subclass ProxyObject).  A spatial origin for PartLists and container for
    references to its PairedPartInstances

Oligo --> Strand (subclass ProxyObject)

Part --> Block (name debatable) (subclass AbstractAssembly)
    Blocks are really just a subclass of assembly where virtual helices can live

Assembly --> Assembly (subclass AbstractAssembly)

    Can be assemblies of assemblies
    Can be multiple assemblies per virtualhelix
    Can be collections of virtualhelices


NEW STUFF
AbstractAsseblyInstace (subclass ObjectInstance)

PartInstance (subclass ObjectInstance) --> Pointer to a part or all of another Part / PartInstance.
    offset
    length

PairedPart (subclass AbstractAssembly) --> assembly containing 1-2 PartInstances paired with each other
    
PairedPartInstance (subclass AbstractAssemblyInstance)

    * When you import a plasmid and want to reference a piece of it you get:
        * 1 PairedPart
        * 1-2 PartInstances (depending whether you wat single or double stranded)
    * And you place a PairedPartInstance onto a VirtualHelix of a Block
    * You get all of the features that overlap the reference region
    * If you want to break the share link, you create a new:
        * PairedPart
        * PairedPartInstance
        * 1 or 2 Parts (Depending on whether you want to edit one or both Parts)
        * 1 or 2 PartInstances (etc)


Every Type of object can have features/annotations
