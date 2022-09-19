# PyWiki

**PyWiki** is a very basic implementation of Wiki. Users could view and modify their markdown files. All markdown files can be stored under `repo` directory  and Users can organize them with sub-directories.

## Installation

```shell
# clone the repository
git clone https://github.com/Erickrus/pywiki

# install required packages
sudo pip3 install -r requirements.txt

# install mathjax
wget https://github.com/mathjax/MathJax/archive/2.7.5.zip
unzip 2.7.5.zip -d static/js
rm 2.7.5.zip

```

## Run
```shell
python3 pywiki.py
```

You can open with your browser and access http://localhost:8080/static/index.html

## Usage
### Browse
For normal md file, you can just **browse** it with url, put the relative path name e.g. `/dir1/dir2/test.md`. 

If you want to go back, just click `Back` button.

### Find
If you want to find by keywords, you can input `find: keyword1 keyword2`. Then hit go to search. 

Notice find is just search files one by one. The search engine is not leveraged yet. It could be slow when scale out.

## Edit
In `Edit` tab, you will find the corresponding markdown in text format. It can be edited and saved.
