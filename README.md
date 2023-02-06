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
- If `new_version` is empty, all versions beside `base_version` in the library's versionMapping will be considered as `new_version`.



We provide several subjects to demonstrate LooCo's usage, i.e.,

- project **TweetTel** upon library **requests** (base version: 2.27.1)
- project  **BeerClub** upon library **requests** (base version: 2.25.1)
- project **download-tweets-ai-text-gen** upon library **twint** (base version: 2.1.4)
- project **vesta** upon library **schedule** (base version: 0.5.0)

*Any identity appearing in the above subjects belongs to the open source project, and is not related to authors.*



### Examples

```shell
python main.py TweetTel requests 2.27.1 2.27.0


# Execute the above code, and the output result is:

# safe to loosen to 2.27.0
```

> Given a specific `new_version` , LooCo will output whether it is safe for the project to use the library with `new_version`. The above example means: for project **TweetTel**, it's safe to loosen the dependency of **requests** to 2.27.0.



```shell
python main.py TweetTel requests 2.27.1


# Execute the above code, and the output result is:

# safe new versions: 2.26.0, 2.27.0
# risky new versions: 2.24.0, 2.25.0, 2.25.1, 2.28.0, 2.28.1
```

> If `new_version` is empty, all versions beside `base_version` in the library's versionMapping will be considered as `new_version`. The above example means: for project **TweetTel**, it's safe to loosen the dependency of **requests** to 2.26.0 and 2.27.0, and it's risky to loosen to other versions, i.e., 2.24.0, 2.25.0, 2.25.1, 2.28.0, and 2.28.1.



```shell
python main.py BeerClub requests 2.25.1

# Execute the above code, and the output result is:

# suggest to remove
```

> If Looco detect no call to the library in the project, Looco will suggest to remove the dependency on the   library. The above example means: for project **BeerClub**, LooCo suggest to remove the dependency on requests.





*All subjects are open source and can be downloaded according to the commit ID or the version. Due to the requirement of extremely large storages (hundreds of GB), they are not placed on this website for now. We plan to share them upon requests in future. You can also use the subject name in either SubjectA or SubjectB used in our subject to search and download on your own from the website.*