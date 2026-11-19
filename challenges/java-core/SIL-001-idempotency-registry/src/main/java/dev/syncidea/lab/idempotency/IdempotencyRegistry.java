package dev.syncidea.lab.idempotency;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

/** Реестр принятия ключей на фиксированный TTL в пределах одного процесса. */
public final class IdempotencyRegistry {
    private final Duration ttl;
    private final Clock clock;
    private final Map<String, Instant> expiresAtByKey = new HashMap<>();

    public IdempotencyRegistry(Duration ttl, Clock clock) {
        this.ttl = Objects.requireNonNull(ttl, "ttl");
        this.clock = Objects.requireNonNull(clock, "clock");
        if (ttl.isZero() || ttl.isNegative()) {
            throw new IllegalArgumentException("ttl must be positive");
        }
    }

    /** Возвращает true, если вызов открыл новое окно для ключа. */
    public boolean tryAcquire(String key) {
        Objects.requireNonNull(key, "key");
        if (key.isBlank()) {
            throw new IllegalArgumentException("key must not be blank");
        }

        synchronized (expiresAtByKey) {
            Instant now = clock.instant();
            Instant expiresAt = expiresAtByKey.get(key);
            if (expiresAt != null && now.isBefore(expiresAt)) {
                return false;
            }
            expiresAtByKey.put(key, now.plus(ttl));
            return true;
        }
    }
}
