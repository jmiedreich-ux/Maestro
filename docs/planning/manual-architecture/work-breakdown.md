# Planning Maestro development features

Use this guide for breaking down the work of building Maestro itself. Maestro's future project-planning workflow is specified separately in the product architecture.

## Plan the next checkpoint

1. Start with the ordered outcomes in [the development roadmap](../../../plan/outcomes.md).
2. List and prove blocking prerequisites, including host setup, credentials, real agent routes, installation, data, and observability. Record each assumption and its proving feature or explicit exclusion.
3. Define complete features for the next usable result. Each feature names its real entry point, visible or durable result, key connections, permitted paths, environment prerequisites, owner, and verification.
4. Check dependencies against existing code and active feature results. Walk through the feature in pseudocode or a concrete sequence before coding to uncover missing contracts, errors and scope.
5. Group finished features into a small milestone with one plain-language acceptance sentence, assembled QA and a merge point.

Only the next milestone's features need detailed specifications. Keep later outcomes and potential features coarse. Do not create a fixed packet count or work-packet files upfront.

## During feature delivery

The feature owner inspects the real code, saves a small packet breakdown within the feature plan, and continues without a packet approval gate. Each packet states exact files, intended change and a quick check, especially when delegated to a smaller local model. The owner verifies the packets form the full working flow. Review and merge the feature as a whole.

New findings follow the [delivery boundaries](packet-rules.md). A missing prerequisite blocks only affected work. A change to an outcome goes to the Owner; a useful extra goes into future work. Do not split or rename a feature to reset a review limit.
