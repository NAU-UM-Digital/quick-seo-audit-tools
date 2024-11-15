# Quick SEO Audit Tools

## Summary

CLI tools to quickly collect data and help audit webpages with tedious SEO tasks in mind.

When creating, auditing, and QA-ing web content with accessibility, user experience, organic search, and other goals in mind, there are many tools that help identify problems on a site—tools like Semrush, SiteImprove, and Google Search Console all play an important role in everyday auditing workflows. However, we find that many of these tools do not provide the granularity or prompt collection of data to quickly and efficiently resolve pressing issues across our sites.

To help fill this gap, Quick SEO Audit Tools provides an extendable base to quickly audit copy, links, and other important site elements from the command line.

## .devcontainer spec

Uses the standard devcontainer spec to create a consistent development environment. If you'd prefer to install the dependencies mnually, I'd recommend checking out the .devcontainer folder as a reference to make sure you have the proper dependencies installed.

## Building and installing the package

### Build

```python3 -m build```

### Install

```pip3 install /path/to/dist/file```

## Development

seo-tools uses relative module imports, so if you want to run changes without building you'll need to use `python3 -m` from within the src directory.