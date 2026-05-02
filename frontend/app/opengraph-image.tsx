import {
  BRAND_OG_ALT,
  BRAND_OG_SIZE,
  brandOpenGraphImageResponse,
} from "@/lib/brand-opengraph";

export const alt = BRAND_OG_ALT;
export const size = BRAND_OG_SIZE;
export const contentType = "image/png";

export default function OpenGraphImage() {
  return brandOpenGraphImageResponse();
}
