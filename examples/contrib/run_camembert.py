import torch

from transformers.modeling_camembert import CamembertForMaskedLM
from transformers.tokenization_camembert import CamembertTokenizer


def fill_mask(masked_input, model, tokenizer, topk=5):
    # Adapted from https://github.com/pytorch/fairseq/blob/master/fairseq/models/roberta/hub_interface.py
    assert masked_input.count("<mask>") == 1
    input_ids = torch.tensor(tokenizer.encode(masked_input, add_special_tokens=True)).unsqueeze(0)  # Batch size 1
    logits = model(input_ids)[0]  # The last hidden-state is the first element of the output tuple
    masked_index = (input_ids.squeeze() == tokenizer.mask_token_id).nonzero().item()
    logits = logits[0, masked_index, :]
    prob = logits.softmax(dim=0)
    values, indices = prob.topk(k=topk, dim=0)
    topk_predicted_token_bpe = " ".join(
        [tokenizer.convert_ids_to_tokens(indices[i].item()) for i in range(len(indices))]
    )
    masked_token = tokenizer.mask_token
    topk_filled_outputs = []
    for index, predicted_token_bpe in enumerate(topk_predicted_token_bpe.split(" ")):
        predicted_token = predicted_token_bpe.replace("\u2581", " ")
        if " {0}".format(masked_token) in masked_input:
            topk_filled_outputs.append(
                (
                    masked_input.replace(" {0}".format(masked_token), predicted_token),
                    values[index].item(),
                    predicted_token,
                )
            )
        else:
            topk_filled_outputs.append(
                (masked_input.replace(masked_token, predicted_token), values[index].item(), predicted_token,)
            )
    return topk_filled_outputs



def fill_many_masks(masked_input, model, tokenizer, topk=3, argmax=False, beam_search=False):
    assert argmax and not beam_search
    # Adapted from https://github.com/pytorch/fairseq/blob/master/fairseq/models/roberta/hub_interface.py
    #assert masked_input.count("<mask>") == 1
    input_ids = torch.tensor(tokenizer.encode(masked_input, add_special_tokens=True)).unsqueeze(0)  # Batch size 1
    logits = model(input_ids)[0]  # The last hidden-state is the first element of the output tuple
    masked_index = (input_ids.squeeze() == tokenizer.mask_token_id).nonzero().squeeze()
    logits = logits[0, masked_index, :]
    prob = logits.softmax(dim=-1)
    if argmax == True:
      values, indices = prob.topk(k=1, dim=-1) ## For now we just take the argmax
      if indices.dim()>1:
        indices = indices.squeeze(0)
      parts = masked_input.split("<mask>")
      output = [None]*(len(parts)+len(indices))
      output[::2] = parts
      output[1::2] = [token.replace("\u2581", " ") for token in tokenizer.convert_ids_to_tokens(indices)]
      output = " ".join(output)
      return output
    else:
      masked_token = tokenizer.mask_token
      topk_filled_outputs = []
      for index, predicted_token_bpe in enumerate(topk_predicted_token_bpe.split(" ")):
          predicted_token = predicted_token_bpe.replace("\u2581", " ")
          if " {0}".format(masked_token) in masked_input:
              topk_filled_outputs.append(
                  (
                      masked_input.replace(" {0}".format(masked_token), predicted_token),
                      values[index].item(),
                      predicted_token,
                  )
              )
          else:
              topk_filled_outputs.append(
                  (masked_input.replace(masked_token, predicted_token), values[index].item(), predicted_token,)
              )
    return topk_filled_outputs



tokenizer = CamembertTokenizer.from_pretrained("camembert-base")
model = CamembertForMaskedLM.from_pretrained("camembert-base")
model.eval()

masked_input = "Le camembert est <mask> :)"
print(fill_mask(masked_input, model, tokenizer, topk=3))
