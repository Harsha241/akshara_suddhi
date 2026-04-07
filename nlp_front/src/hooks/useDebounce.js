import { useCallback, useRef } from "react";

/**
 * Returns a debounced version of `fn`.
 * Resets the timer on every call; fires after `delay` ms of silence.
 */
export default function useDebounce(fn, delay = 400) {
  const timer = useRef(null);

  return useCallback(
    (...args) => {
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => fn(...args), delay);
    },
    [fn, delay]
  );
}
