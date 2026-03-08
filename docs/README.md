# Documentation Hub

This directory is the entry point for collaborators who need to understand the repository without reading the implementation first.

## Audience-specific guides

- [`ja/README.md`](ja/README.md): Japanese guide for CMIS Lab, The University of Tokyo
- [`en/README.md`](en/README.md): English guide for LAMSADE collaborators

Maintenance note: `ja/README.md` and `en/README.md` should stay aligned in content. Update both when changing onboarding information, scope, or navigation.

## Shared technical guides

- [`architecture.md`](architecture.md): current code architecture and module map
- [`research-workflow.md`](research-workflow.md): recommended workflow for synthetic and real-data studies

## Detailed technical archive

The implementation still lives under [`../legacy/`](../legacy/). When you need rule-by-rule or axiom-by-axiom detail, continue to:

- [`../legacy/README.md`](../legacy/README.md)
- [`../legacy/docs/README.md`](../legacy/docs/README.md)
- [`../legacy/docs/ranking/README.md`](../legacy/docs/ranking/README.md)
- [`../legacy/docs/axioms/README.md`](../legacy/docs/axioms/README.md)

## Suggested reading order

1. Read the audience-specific guide.
2. Read [`architecture.md`](architecture.md) for the code layout.
3. Read [`research-workflow.md`](research-workflow.md) for the experiment flow.
4. Use the `legacy/docs` materials as appendices when implementation detail is needed.
