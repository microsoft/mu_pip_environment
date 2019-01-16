

# The Omnicache or how I learned to stop worrying and love the allrepo

## The Genesis
Many repos in the Project Mu tree have common roots and share a very similar codebase. In order to speed up clone times for our CI builds as well as for personal use, we realized you can clone a repo using a reference repository.

```bash
git clone {{URL}} --reference ../some-directory
```

Another feature that came to light is that you can use git to create an omnirepostitory. You can have all the objects stored into one place and git will query this repo for any objects it wishes to fetch and if they aren't found, it will then request them from upstream.

We created some helper functions to wrap around this. It can be called by omnicache.

## Creating a new omnicache
```bash
omnicache --init ../omnicache
```
You can optionally use
```bash
omnicache --new ../omnicache
```
The difference between the two is that new will fail if something exists there, init does not.

## Feeding- I mean, Adding to the omnicache
```bash
omnicache -a <name> <url> <Sync tags optional default=False> ../omnicache
omnicache --add <name> <url> <Sync tags optional default=False> ../omnicache
```
  (Either of these will work)

## Updating the omnicache
Now that you're a proud owner of an omnicache, you need to take care to update it semi-regularly.
```bash
omnicache --update ../omnicache
omnicache -u ../omnicache
```
  (Either of these will work)

## Know what's in the cache
You can find out what is in your cache by listing it's contents.
```bash
omnicache --list ../omnicache
```

## Assimilation into the Omnicache
Sometimes you have a folder where all the repos are already cloned (either as submodules or seperate folders). You can scan them all into the omnicache by using the scan feature.
```bash
omnicache --scan ../folder ../omnicache
```
This will add unique repos/submodules that it finds in the top level folders in ../folder. Unique is determined by URL.

## Fighting back against the Omnicache
If your omnicache has grown a touch too powerful, you can take control back in your life by removing items from the cache.
```bash
omnicache --remove {{name_of_repo}} ../omnicache
omnicache -r {{name_of_repo}} ../omnicache
```

## Using the Omnicache
Many of the tools in Project Mu are equipped to handle the omnicache and details on how to use them can be found in their respective documentations or help menus.
