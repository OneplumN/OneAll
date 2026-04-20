type AccessTokenListener = (token: string | null) => void;

let currentAccessToken: string | null = null;
const listeners = new Set<AccessTokenListener>();

export function getAccessToken() {
  return currentAccessToken;
}

export function setAccessToken(token: string | null) {
  currentAccessToken = token;
  listeners.forEach((listener) => listener(token));
}

export function subscribeAccessToken(listener: AccessTokenListener) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
