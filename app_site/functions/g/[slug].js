import { reviewRedirect } from "../api/_review.js";
export const onRequest = (ctx) => reviewRedirect(ctx, "google");
