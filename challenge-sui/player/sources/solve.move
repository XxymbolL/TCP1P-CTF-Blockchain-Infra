/// Player solution module.
/// This module demonstrates how a player would interact with the challenge
/// via the Sui CLI or SDK. The actual solve is done via on-chain transaction.
///
/// Usage via Sui CLI:
///   sui client call --package <PACKAGE_ID> --module challenge \\
///     --function solve --args <CHALLENGE_OBJECT_ID> <ANSWER> --gas-budget 10000000
module solution::solve {
    // This file serves as documentation for players.
    // The challenge is solved by calling challenge::challenge::solve(challenge_obj, 42)
    // directly on-chain via Sui CLI or SDK — not by compiling this module.
}
