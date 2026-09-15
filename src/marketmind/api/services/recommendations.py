"""Compact-history adapter preserving frozen Item-CF ranking semantics."""
import numpy as np
import pandas as pd
def recommend_compact(bundle,visitor_id,snapshot_timestamp,history_item_ids,k):
    # Registry validation is load-once; request-time scoring never rescans the graph.
    snapshot=pd.Timestamp(snapshot_timestamp)
    if snapshot.tzinfo is None: snapshot=snapshot.tz_localize("UTC")
    else: snapshot=snapshot.tz_convert("UTC")
    snapshot_ms=int(snapshot.timestamp()*1000)
    if snapshot_ms<bundle.training_cutoff_ms: raise ValueError("snapshot precedes artifact training cutoff")
    history=sorted(set(map(int,history_item_ids))); history_set=set(history); known=[x for x in history if x in bundle.item_to_index]
    # Production requests cannot predate the all-history cutoff, so the trained
    # catalog is fully available. The registry pre-sorts fallback popularity once.
    available=set(map(int,bundle.item_ids)); scores={}
    for item in known:
        index=bundle.item_to_index[item]; start,end=bundle.neighbor_indptr[index:index+2]
        for neighbor,similarity in zip(bundle.neighbor_indices[start:end],bundle.neighbor_similarities[start:end]):
            candidate=int(bundle.item_ids[neighbor])
            if candidate in available: scores[candidate]=scores.get(candidate,0.)+float(similarity)
    selected=sorted(scores,key=lambda x:(-scores[x],x))[:k]; sources=["collaborative"]*len(selected); values=[scores[x] for x in selected]; chosen=set(selected)
    popularity=getattr(bundle,"_api_popularity_order",None)
    if popularity is None:
        popularity=tuple(sorted(zip(map(int,bundle.popularity_item_ids),map(int,bundle.popularity_counts)),key=lambda x:(-x[1],x[0])))
    for item,count in popularity:
        if len(selected)>=k: break
        if item not in chosen:
            selected.append(item); sources.append("popularity_fill"); values.append(float(count)); chosen.add(item)
    reason="" if history_set and known and scores else ("no_history" if not history_set else "no_collaborative_history" if not known else "no_available_collaborative_candidates")
    rows=[{"visitor_id":int(visitor_id),"snapshot_timestamp":snapshot,"rank":rank,"item_id":item,"score":float(score),"recommendation_source":source,"seen_before":item in history_set} for rank,(item,score,source) in enumerate(zip(selected,values,sources),1)]
    return rows,("fallback" if reason else "personalized"),reason
def run(request,bundle): return recommend_compact(bundle,request.visitor_id,request.snapshot_timestamp,request.history_item_ids,request.k)
