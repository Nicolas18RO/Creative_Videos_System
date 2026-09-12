import { apiPost } from "../../../shared/api/client";
import type { SearchRequestDto, SearchResponseDto } from "../types/studio";

export async function postSearch(body: SearchRequestDto): Promise<SearchResponseDto> {
  return apiPost<SearchResponseDto>("/search", body);
}
