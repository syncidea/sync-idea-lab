package dev.syncidea.lab.idempotency;

import java.time.Clock;
import java.time.Duration;
import java.util.Objects;

/** Реестр принятия ключей на фиксированный TTL. Реализуйте контракт из README. */
public final class IdempotencyRegistry {
    private final Duration ttl;
    private final Clock clock;

    public IdempotencyRegistry(Duration ttl, Clock clock) {
        this.ttl = Objects.requireNonNull(ttl, "ttl");
        this.clock = Objects.requireNonNull(clock, "clock");
        if (ttl.isZero() || ttl.isNegative()) {
            throw new IllegalArgumentException("ttl must be positive");
        }
    }

    /** @return true, если ключ принят; false, если предыдущий TTL ещё действует. */
    public boolean tryAcquire(String key) {
        Objects.requireNonNull(key, "key");
        if (key.isBlank()) {
            throw new IllegalArgumentException("key must not be blank");
        }
        // TODO: реализуйте потокобезопасную регистрацию с TTL.
        throw new UnsupportedOperationException("Implement SIL-001");
    }
}
