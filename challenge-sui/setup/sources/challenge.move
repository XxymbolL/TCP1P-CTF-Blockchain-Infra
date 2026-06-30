module challenge::challenge {
    use sui::transfer;
    use sui::tx_context::TxContext;

    /// The secret answer. Players must discover this value.
    /// (Hint: it's the Answer to the Ultimate Question of Life, the Universe, and Everything.)
    const SECRET: u64 = 42;

    /// Challenge state object — owned by the deployer (admin).
    public struct Challenge has key {
        id: UID,
        solved: bool,
    }

    /// Create and share a new unsolved Challenge object.
    /// Anyone can then call `solve` on it.
    /// Called by the instancer after publishing the package.
    public fun initialize(ctx: &mut TxContext) {
        let challenge = Challenge {
            id: object::new(ctx),
            solved: false,
        };
        transfer::share_object(challenge);
    }

    /// Solve the challenge by providing the correct secret answer.
    /// Anyone who knows the secret can call this on the Challenge object.
    public fun solve(challenge: &mut Challenge, answer: u64) {
        assert!(answer == SECRET, 0);
        challenge.solved = true;
    }

    /// Check whether the challenge has been solved.
    public fun is_solved(challenge: &Challenge): bool {
        challenge.solved
    }

    #[test_only]
    public fun destroy(challenge: Challenge) {
        let Challenge { id, solved: _ } = challenge;
        object::delete(id);
    }

    #[test]
    fun test_solve_correct() {
        use sui::tx_context;
        let ctx = tx_context::dummy();
        let mut chal = Challenge {
            id: object::new(&mut ctx),
            solved: false,
        };
        solve(&mut chal, 42);
        assert!(is_solved(&chal), 1);
        destroy(chal);
    }

    #[test]
    #[expected_failure(abort_code = 0)]
    fun test_solve_wrong() {
        use sui::tx_context;
        let ctx = tx_context::dummy();
        let mut chal = Challenge {
            id: object::new(&mut ctx),
            solved: false,
        };
        solve(&mut chal, 0);
        destroy(chal);
    }
}
