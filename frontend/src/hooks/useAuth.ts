import { useAuth0 } from "@auth0/auth0-react"
import { setApiTokenProvider } from "../lib/api"

export function useAuth() {
  const {
    user: auth0User,
    isLoading,
    isAuthenticated,
    loginWithRedirect,
    logout,
    getAccessTokenSilently,
  } = useAuth0()

  // Wire up the token provider so all api.ts calls attach the Bearer token
  if (isAuthenticated) {
    setApiTokenProvider(getAccessTokenSilently)
  }

  // Normalise to the shape the rest of the app expects (user.id, user.email)
  const user = auth0User
    ? { id: auth0User.sub!, email: auth0User.email ?? "", ...auth0User }
    : null

  const signIn = () => loginWithRedirect()
  const signUp = () =>
    loginWithRedirect({ authorizationParams: { screen_hint: "signup" } })
  const signOut = () =>
    logout({ logoutParams: { returnTo: window.location.origin } })

  return { user, loading: isLoading, signIn, signUp, signOut }
}
