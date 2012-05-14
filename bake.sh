#! /bin/bash
git checkout master README.md
#git checkout master CHANGELOG.md
markdown2 README.md > tmp_readme
#markdown2 CHANGELOG.md > tmp_log
cat templates/header.html tmp_readme  templates/footer.html > index.html
rm tmp_readme 
git add index.html
git commit -m "Updated Readme from master"
git push -u origin gh-pages
