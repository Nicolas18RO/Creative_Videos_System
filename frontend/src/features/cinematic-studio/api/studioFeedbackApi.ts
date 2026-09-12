import { apiPost } from "../../../shared/api/client";
import type { FeedbackRequestDto, FeedbackResponseDto } from "../types/studio";

export async function postFeedback(body: FeedbackRequestDto): Promise<FeedbackResponseDto> {
  return apiPost<FeedbackResponseDto>("/feedback", body);
}
