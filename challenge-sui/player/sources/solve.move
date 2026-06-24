/// Player solution module.
/// The server compiles this with the challenge and runs a test to verify it solves.
module solution::solve {
    use challenge::challenge;
    use sui::tx_context::TxContext;

    /// Your exploit: receive the Challenge object and solve it.
    public fun solve(challenge: &mut challenge::Challenge, _ctx: &mut TxContext) {
        challenge::solve(challenge, _ctx);
    }
}
