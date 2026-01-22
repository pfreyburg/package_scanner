FROM image_a

COPY . .

FROM image_b as stage_a

RUN pip install -r requirements.txt

FROM image_c:latest AS stage_b