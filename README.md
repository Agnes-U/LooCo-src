# LooCo



## Prerequisites

1. Python 3.8
2. Pre-downloaded projects and different versions of libraries.
   - Several projects and libraries for demonstration have been downloaded in "projects" and "libraries".
3. Fill each needed library version and its path in "libraries/versionMapping.json".
   - `library:{v1:path1, v2:path2, ...}`



## How to use it

```
cd src
```

You can use the following command to run LooCo.

```
python main.py project_folder library_name base_version (new_version)
```

- `project_folder` can be an absolute path or folder name under "projects".
- If `new_version` is empty, all versions beside `base_version` in the library's versionMapping will be considered as new_version.

For example,

```shell
python main.py TweetTel requests 2.27.1
# or python main.py TweetTel requests 2.27.1 2.28.0

python main.py download-tweets-ai-text-gen twint 2.1.4

python main.py vesta schedule 0.5.0

python main.py django_ecommerce requests 2.25.1
```



*All subjects are open source and can be downloaded according to the commit ID or the version. Due to the large storage (hundreds of GB), they are not placed on this website for now, and we can also share them if necessary in the future.*