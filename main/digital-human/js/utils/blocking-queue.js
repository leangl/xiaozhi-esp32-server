export default class BlockingQueue {
    #items   = [];
    #waiters = [];          // {resolve, reject, min, timer, onTimeout}

    /* One-shot barrier for an empty queue */
    #emptyPromise = null;
    #emptyResolve = null;

    /* Producer: enqueue data */
    enqueue(item, ...restItems) {
        if (restItems.length === 0) {
            this.#items.push(item);
        }
        // Handle additional arguments as a batch
        else {
            const items = [item, ...restItems].filter(i => i);
            if (items.length === 0) return;
            this.#items.push(...items);
        }
        // Release all callers waiting on the empty-queue barrier
        if (this.#emptyResolve) {
            this.#emptyResolve();
            this.#emptyResolve = null;
            this.#emptyPromise = null;
        }

        // Wake all pending waiters
        this.#wakeWaiters();
    }

    /* Consumer: wait for min items or timeout milliseconds */
    async dequeue(min = 1, timeout = Infinity, onTimeout = null) {
        // 1. If empty, wait for the first item (all callers share one promise)
        if (this.#items.length === 0) {
            await this.#waitForFirstItem();
        }

        // Ready immediately
        if (this.#items.length >= min) {
            return this.#flush();
        }

        // Wait for more items
        return new Promise((resolve, reject) => {
            let timer = null;
            const waiter = { resolve, reject, min, onTimeout, timer };

            // Timeout handling
            if (Number.isFinite(timeout)) {
                waiter.timer = setTimeout(() => {
                    this.#removeWaiter(waiter);
                    if (onTimeout) onTimeout(this.#items.length);
                    resolve(this.#flush());
                }, timeout);
            }

            this.#waiters.push(waiter);
        });
    }

    /* Create the empty-queue barrier */
    #waitForFirstItem() {
        if (!this.#emptyPromise) {
            this.#emptyPromise = new Promise(r => (this.#emptyResolve = r));
        }
        return this.#emptyPromise;
    }

    /* Internal: check satisfied waiters after each data change */
    #wakeWaiters() {
        for (let i = this.#waiters.length - 1; i >= 0; i--) {
            const w = this.#waiters[i];
            if (this.#items.length >= w.min) {
                this.#removeWaiter(w);
                w.resolve(this.#flush());
            }
        }
    }

    #removeWaiter(waiter) {
        const idx = this.#waiters.indexOf(waiter);
        if (idx !== -1) {
            this.#waiters.splice(idx, 1);
            if (waiter.timer) clearTimeout(waiter.timer);
        }
    }

    #flush() {
        const snapshot = [...this.#items];
        this.#items.length = 0;
        return snapshot;
    }

    /* Current buffered item count (excluding waiters) */
    get length() {
        return this.#items.length;
    }

    /* Clear items while retaining the array reference and pending waiters */
    clear() {
        this.#items.length = 0;
    }
}
