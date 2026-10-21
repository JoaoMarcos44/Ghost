# B4: Subdirectory homepage links with query strings

![B4 infographic](infographic.png)

**Architecture:** Admin stores navigation links relative to the configured site base. The public site adds that base path when it renders a link.

**Problem:** On a site at `/blog/`, a homepage URL such as `/blog?ref=menu` keeps `/blog` in the saved value. Rendering adds the base path again and produces `/blog/blog?ref=menu`.

**Proposed solution:** Recognize the homepage path without its trailing slash, save it as `/`, and preserve its query string or fragment. The change is proposed and not merged.

**Validation shown:** Query, fragment, combined query-and-fragment, and child-path controls. The infographic describes proposed checks, not a completed test run.
