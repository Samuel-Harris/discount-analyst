import { WORKFLOW_RUNS_LIST_KEY, workflowRunDetailKey } from "./queryKeys";

type InvalidateHandler = () => void | Promise<void>;

const handlersByKey = new Map<string, Set<InvalidateHandler>>();

function touchKey(key: string, handler: InvalidateHandler): () => void {
  let bucket = handlersByKey.get(key);
  if (!bucket) {
    bucket = new Set();
    handlersByKey.set(key, bucket);
  }
  bucket.add(handler);
  return () => {
    bucket!.delete(handler);
    if (bucket!.size === 0) handlersByKey.delete(key);
  };
}

/** Subscribe a running query to explicit invalidation for its key. */
export function subscribeQueryInvalidation(
  queryKey: string,
  onInvalidate: InvalidateHandler,
): () => void {
  return touchKey(queryKey, onInvalidate);
}

export async function invalidateQueryKey(queryKey: string): Promise<void> {
  const bucket = handlersByKey.get(queryKey);
  if (!bucket?.size) return;
  await Promise.all([...bucket].map((fn) => Promise.resolve(fn())));
}

export async function invalidateQueryKeyPrefix(prefix: string): Promise<void> {
  const tasks: Promise<unknown>[] = [];
  for (const key of handlersByKey.keys()) {
    if (key.startsWith(prefix)) {
      const bucket = handlersByKey.get(key);
      if (bucket?.size) {
        tasks.push(Promise.all([...bucket].map((fn) => Promise.resolve(fn()))));
      }
    }
  }
  await Promise.all(tasks);
}

/** After list-affecting mutations (create, delete, etc.). */
export async function invalidateWorkflowRunsList(): Promise<void> {
  await invalidateQueryKey(WORKFLOW_RUNS_LIST_KEY);
}

/** After a specific workflow run may have changed on the server. */
export async function invalidateWorkflowRunDetail(
  workflowRunId: string,
): Promise<void> {
  await invalidateQueryKey(workflowRunDetailKey(workflowRunId));
}

/** When any run’s summary row may have changed without knowing the id (rare). */
export async function invalidateAllWorkflowRunDetails(): Promise<void> {
  await invalidateQueryKeyPrefix("workflowRuns:detail:");
}

/** Test-only: clear registry between cases when hooks may not unmount cleanly. */
export function resetQueryInvalidationRegistryForTests(): void {
  handlersByKey.clear();
}
