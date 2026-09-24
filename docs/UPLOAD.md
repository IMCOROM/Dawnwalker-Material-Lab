# Upload to GitHub and reply to the site

1. Extract the source ZIP locally.
2. Create a new GitHub repository, for example `Dawnwalker-Material-Lab`. Make it
   public if the site's reviewer needs public access. Do not initialize it with
   another README.
3. Upload the **contents** of this source folder, so `README.md`, `build.ps1`,
   `MaterialLab.spec`, and `src/` appear at the repository root. Do not upload just
   the source ZIP: reviewers should be able to browse the individual source files.
4. Commit the upload with a message such as `Publish v0.19 source and build instructions`.
5. Copy the repository URL and the commit permalink (open the commit and copy its URL).
6. Send the reply below after replacing both placeholders.

Do not add `Projects`, the full `AssetLibrary`, `.venv`, `dist`, the old app folder,
game keys, or personal files. The source package already contains the intended
review documents and complete application source. GitHub Desktop can publish the
same folder if browser uploads are inconvenient.

## Suggested reply

> Hi, I've published the full application source for Dawnwalker Material Lab v0.19 here:
>
> REPOSITORY_URL
>
> This commit corresponds to the source used for the submitted Windows application:
>
> COMMIT_URL
>
> The repository includes detailed Windows build instructions in `docs/BUILD.md`,
> pinned Python build dependencies, the PyInstaller configuration, build and runtime
> check scripts, a review guide, and a SHA-256 manifest of every file in the submitted
> no-nested-ZIP release.
>
> The application can be built independently from source. The full portable release
> also contains external tools and game-derived assets; these are explicitly documented
> in `docs/DEPENDENCIES.md`, including components for which source/provenance is not
> available in this repository. The resource assembly script verifies those files
> against the submitted release instead of reusing its application executable.
>
> Please let me know if you need any additional information for your review.

No GitHub account credentials or publication have been performed by these scripts.
