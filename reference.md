# Component definition

Component contains three mainly sections:
1. HTML basic skeleton
2. Styles definition
3. Python-script events and behaviors 

## HTML

Contains component skeleton.
```html
<button extend:BaseUI type="button" set:disabled="{not $enabled}" on:click="{$onClick()}">
    {#if $image}<img src="{$image}">{/if}
    <span ref:caption>{$caption}</span>
</button>
``` 

Special attributes:
  - **extend:name** - Points to base component to extend.
  - **set:attribute** - set boolean condition to enable attribute.
  - **on:click** - attach onClick event to object
  - **class:name** - enable class by boolean trigger
  - **ref:caption** - set special name for node to direct access from event via **refs** collection
  
Inline meta operators:
  - ``{#if ...}{/if}`` - conditional substitution
  - ``{#for ... in ...}{/for}`` - loops
  
## CSS styles

Styles definition similar to regular HTML. Styles are localized to current object definition, including tags and classes.

## Events

# Streaming commands

Each client session establish two permanent connections:
1. Streaming UI and data updates from backend to frontend. Let's name it **protocol A**.
2. Streaming backend command calls and updated data from frontend to backend. Let's name it **protocol B** respectively.

Obviously, both connections are initiated by client side.
Each stream have two specifications: one for **request** and one for **response**. Data stream serialized by
[BSDF](https://bsdf.readthedocs.io/index.html) binary format. It is compatible with any Object-Dict-JSON structure.
I suggest to describe protocol details using JSON representation.

Each request command has regular simple format:
```json
{
    "t": "timestamp",
    "c": "command_name",
    "d": "datas..."
}
```  
Each response has format:
```json
{
    "t": "timestamp", //related to request
    "d": "datas..."
}
```

## Protocol A specification
 
### Handshake

Used to initiate connection.

  - **Command**: ``HELLO``
  - **Data**: empty
  - **Expected response**: string ``HELLO``

### Restart

Used to (re)start application, and query main content to construct ``BODY`` content.

  - **Command**: ``RESTART``
  - **Data**: empty
  - **Response**: Root DOM
  
### Shutdown

Used to gracefully close client session.

  - **Command**: ``SHUTDOWN``
  - **Data**: empty
  - **Response**: none

### Click event

Process click event.

  - **Command**: ``CLICK``
  - **Data**: node ID
  - **Response**: none

  
### DOM updates stream

DOM updates coming regularly with regards to backend requests by protocol B and other scheduled behaviors.
DOM updates specified by list of object changes and linked child objects.

Object list:
```json
{
    "m": "update mode letter",
    "l": ["object1", "object2", "object3"]
}
```
Update mode:
  - **c** - create objects
  - **u** - update objects
  - **d** - delete objects

Object node:
```json
{
    "tagName": "p",
    "id": "o123",
    "children": ["id1", "id2", "id3"],
    "attributes": { },
    "text": "container text content"
}
```
