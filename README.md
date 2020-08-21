# pantra
Python Full-stack Framework

*Inspired by Svelte, React, Django, Web2Py and Zen of Python*

# What is it?

Component based Web framework with specific features:
1. HTML-like definition with SCSS styling
2. Web Socket protocol for DOM processing
3. Python language for backend and frontend
4. Portable database schema compatible with ORM (Pony, Django, etc)
5. I18n in gettext-compatible style  

```HTML
<h1>Choose your destiny</h1>
<div class="list">
{{#for destiny in destiny_set}}
  <button type="button" on:click="choose" data:value="{destiny}">{{destiny}}</button>
{{/for}}
</div>
<div class="verdict">{{chosen}}</div>

<style type="text/scss">
.list {
    display: flex;
    flex-flow: row;

    > button {
        padding: 0.3rem 1rem;
    }
}
.verdict {
    font-weight: bold;
    font-style: italic;
}
</style>

<python>
from apps.destiny.models import *
from pantra.ctx import *

chosen: str = 'Make a choice...'

@db_session
def destiny_set():
    for row in db.Destiny.select():
        yield row.title

def choose(node):
    ctx['chosen'] = node.data.value
</python>
```

# Why another framework?

I need flexible, simple and rich tool to perform modern dynamic Web application.
  - I want power of NodeJS, but prefer Python and I am Zen-follower
  - I want to change the HTTP mass query conception to Web Socket's constant connection
  - I want to manipulate solid chunks of business logic as components (MVC joined in one file)
  - I want to deal with data most natural way, without SQL usage
  - I want advantages of asynchronous programming, but get away coloring with `async`
  - I want it made simple. Enough to teach newbies within shortest learning curve.
  - I want ability to make it scalable and globally infinitely.  

# Installation

It still under active development and does not exist as special PYPI package.
However, feel free to download and make your own Apps experience.

```commandline
mkdir pantra
cd pantra
python -m venv .
git clone https://github.com/zergos/pantra .
pip install -r requirements.txt 
```
Create Postgres local database `bwf` with login and password 'bwf'.
```commandline
python pantra.py migrate.apply system
python pantra.py migrate.apply storage
```
Everything is ready to strart now.
```commandline
python pantra.py run
```

Now, you can open your browser and check demo app by local address <http://localhost:8005/storage>