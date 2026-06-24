module challenge::challenge {
    use sui::object::{Self, UID};
    use sui::tx_context::TxContext;

    /// Challenge state object.
    struct Challenge has key {
        id: UID,
        solved: bool,
    }

    /// Create and return a new unsolved Challenge object.
    /// The caller takes ownership.
    public fun initialize(ctx: &mut TxContext): Challenge {
        Challenge {
            id: object::new(ctx),
            solved: false,
        }
    }

    /// Mark the challenge as solved.
    public fun solve(challenge: &mut Challenge, _ctx: &mut TxContext) {
        challenge.solved = true;
    }

    /// Check if the challenge is solved.
    public fun is_solved(challenge: &Challenge): bool {
        challenge.solved
    }

    #[test_only]
    /// Destroys the challenge object (only available in tests).
    public fun destroy(challenge: Challenge) {
        let Challenge { id, solved: _ } = challenge;
        object::delete(id);
    }
}
