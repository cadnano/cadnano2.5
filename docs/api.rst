.. cadnano api

API
===

See our `Scripting <scripting.html>`_ tutorial to get started.


Packages
--------

.. toctree::
   :maxdepth: 1
   :glob:

   api/cadnano.controllers
   api/cadnano.decorators
   api/cadnano.extras
   api/cadnano.fileio
   api/cadnano.gui
   api/cadnano.oligo
   api/cadnano.part
   api/cadnano.proxies
   api/cadnano.removeinstancecmd
   api/cadnano.strand
   api/cadnano.strandset
   api/cadnano.views

Modules
-------

.. toctree::
   :maxdepth: 1
   :glob:

   api/modules
   api/cadnano.addinstancecmd
   api/cadnano.color
   api/cadnano.docmodscmd
   api/cadnano.document
   api/cadnano.objectinstance
   api/cadnano.removeinstancecmd
   api/cadnano.setpropertycmd
   api/cadnano.undocommand
   api/cadnano.undostack
   api/cadnano.util


Detail
------

Cadnano source code is organized using a **Model-View-Controller** (MVC) design
pattern.

Model
~~~~~

The **model** consists of data structures and algorithms for managing and 
manipulating information related to Cadnano designs. It is a standalone
system and can be used without any graphical user interface, though it is much
more useful and intuitive with a GUI.

Views
~~~~~

`Views <api/cadnano.views.html>`_ are a visual representations of the model state.
Cadnano provides several views of the model, each serving a different purpose.
Most user interaction is done in the `Sliceview <api/cadnano.views.sliceview.html>`_,
is an orthographic 2D projection of DNA helices, and the 
`Pathview <api/cadnano.views.pathview.html>`_, a schematic blueprint of the routes
of individual oligos in a design. The Inspector window is a text-based widget that
consists of the `Outlinerview <api/cadnano.views.outlinerview.html>`_,
a hierarchical listing of the components of a design, and the 
`Propertyview <api/cadnano.views.propertyview.html>`_ which allows for editing
properties of selected components. We have future plans for a 3D view and a console view.

Controllers
~~~~~~~~~~~

`Controllers <api/cadnano.controllers.html>`_ are responsible for setting up and
managing the communication between the model and views.

.. note::
   By a traditional MVC definition, Cadnano views have integrated controller
   functionality, i.e. they interpret user actions and send them to the model.


Signals and Slots
~~~~~~~~~~~~~~~~~

We use Qt's `Signals and Slots <http://doc.qt.io/qt-5/signalsandslots.html>`__
framework. The model is responsible for emitting relevant "signals" when modified,
and the views can subscribe to those signals with local "slots" which are methods
that receive model change information as argments and then decide what to do with
it, for example updating a graphical element to reflect the change, or simply
ignoring it.
