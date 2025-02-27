-- DROP FUNCTION IF EXISTS public.__arches_display_tiledata_compact(jsonb, text, boolean);

CREATE OR REPLACE FUNCTION public.__arches_display_tiledata_compact(
	tiledata jsonb,
	language_id text DEFAULT 'en'::text,
	compact boolean DEFAULT false)
    RETURNS jsonb
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE PARALLEL UNSAFE
AS $BODY$
        DECLARE
            
			
        BEGIN
            -- tiledata in a jsonb object with keys as nodeid and values as the value of the node
            -- all keys in tiledata are uuids of nodes.nodeid
            -- we can get the display value of a node using (nodes.name ->> language_id)

            --replace each uuid key with the display value of the node
            
			RETURN json_build_object(
                c.name ->> language_id, jsonb_object_agg(cnw.label ->> language_id,__arches_get_node_display_value(tiledata, n.nodeid, language_id))
                )
			--RETURN jsonb_object_agg(cnw.label ->> language_id,__arches_get_node_display_value(tiledata, n.nodeid, language_id))
            FROM nodes n
                join public.cards_x_nodes_x_widgets cnw on n.nodeid = cnw.nodeid
				join public.cards c on c.cardid = cnw.cardid
            WHERE n.nodeid IN (
                	SELECT jsonb_object_keys(tiledata)::uuid
            	)
				AND (
                    NOT compact 
                    OR __arches_get_node_display_value(tiledata, n.nodeid, language_id) <> ''::text
                )
			GROUP BY c.name;
            
        END;
        
$BODY$;
